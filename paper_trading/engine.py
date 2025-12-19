from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from paper_trading.db import PaperTradingDB
from paper_trading.fees import calc_fees
from paper_trading.models import (
    Direction,
    OrderCreateRequest,
    OrderCreateResponse,
    OrderStatus,
    OrderType,
    RejectCode,
)
from paper_trading.quote_service import QuoteService
from paper_trading.risk import evaluate_order
from paper_trading.symbols import parse_symbol, tick_round
from paper_trading.time_utils import is_weekday, now_cn


def _uuid() -> str:
    return uuid.uuid4().hex


@dataclass
class PaperTradingEngine:
    db: PaperTradingDB
    quote_service: QuoteService
    settings: Any

    def get_kill_switch(self) -> dict[str, Any]:
        enabled = self.db.get_state("kill_switch") == "1"
        updated_at = self.db.get_state("kill_switch_updated_at") or now_cn().isoformat()
        return {"enabled": enabled, "updated_at": updated_at}

    def set_kill_switch(self, enabled: bool) -> dict[str, Any]:
        self.db.set_state("kill_switch", "1" if enabled else "0")
        self.db.set_state("kill_switch_updated_at", now_cn().isoformat())
        payload = {"enabled": enabled}
        self.db.append_event("KILL_SWITCH", None, payload)

        if enabled:
            # Cancel all open orders immediately (MVP1: no partial fills).
            for order in self.db.list_open_orders():
                self._cancel_order_internal(order["client_order_id"], reason="Kill switch")
        return self.get_kill_switch()

    def create_order(self, req: OrderCreateRequest) -> OrderCreateResponse:
        now = now_cn()
        client_order_id = _uuid()

        if req.order_type == OrderType.LIMIT and req.limit_price is None:
            return OrderCreateResponse(
                client_order_id=client_order_id,
                status=OrderStatus.REJECTED,
                reject_code=RejectCode.QUOTE_INVALID,
                reject_reason="limit_price required for LIMIT order",
            )

        quotes = self.quote_service.fetch_quotes([req.symbol])
        quote = quotes.get(req.symbol)
        if quote is None:
            reject_code = RejectCode.QUOTE_INVALID
            reject_reason = "Quote not available (symbol may be suspended or invalid)"
            self._persist_rejected_order(
                client_order_id=client_order_id,
                req=req,
                price=0.0,
                reject_code=reject_code,
                reject_reason=reject_reason,
            )
            return OrderCreateResponse(
                client_order_id=client_order_id,
                status=OrderStatus.REJECTED,
                reject_code=reject_code,
                reject_reason=reject_reason,
            )

        last = quote.last
        bid1 = quote.bid1 or last
        ask1 = quote.ask1 or last
        prev_close = quote.prev_close
        if prev_close is None:
            reject_code = RejectCode.QUOTE_INVALID
            reject_reason = "prev_close missing"
            self._persist_rejected_order(
                client_order_id=client_order_id,
                req=req,
                price=0.0,
                reject_code=reject_code,
                reject_reason=reject_reason,
            )
            return OrderCreateResponse(
                client_order_id=client_order_id,
                status=OrderStatus.REJECTED,
                reject_code=reject_code,
                reject_reason=reject_reason,
            )

        parsed = parse_symbol(req.symbol)
        if req.order_type == OrderType.AGGRESSIVE:
            submit_price = ask1 if req.direction == Direction.BUY else bid1
            submit_price = tick_round(submit_price)
            time_in_force = "GFD"  # capability-based IOC comes later
            timeout_seconds = int(self.settings.aggressive_timeout_seconds)
        else:
            submit_price = tick_round(float(req.limit_price))
            time_in_force = "GFD"
            timeout_seconds = int(self.settings.limit_timeout_seconds)

        account = self.db.get_account()
        position = self.db.get_position(req.symbol)
        available_qty = int(position["available_quantity"]) if position else 0

        kill_switch = self.db.get_state("kill_switch") == "1"
        daily_trades_count = self.db.count_trades_for_date(now.strftime("%Y-%m-%d"))

        decision = evaluate_order(
            symbol=req.symbol,
            direction=req.direction,
            quantity=req.quantity,
            order_type=req.order_type,
            price=submit_price,
            quote={
                "quote_time": quote.quote_time,
                "prev_close": quote.prev_close,
                "last": quote.last,
                "bid1": bid1,
                "ask1": ask1,
            },
            cash=float(account["cash"]),
            available_quantity=available_qty,
            kill_switch=kill_switch,
            order_value_limit=float(self.settings.order_value_limit),
            daily_trades_count=daily_trades_count,
            daily_trades_warn=int(self.settings.daily_trades_warn),
            daily_trades_reject=int(self.settings.daily_trades_reject),
            quote_max_age_seconds=int(self.settings.quote_max_age_seconds),
            allow_out_of_session=bool(getattr(self.settings, "allow_out_of_session", False)),
            now=now,
        )

        if decision.approved and daily_trades_count > int(self.settings.daily_trades_warn):
            self.db.append_event(
                "RISK_WARN",
                client_order_id,
                {
                    "client_order_id": client_order_id,
                    "warning": "Daily trades above warning threshold",
                    "daily_trades_count": daily_trades_count,
                    "threshold": int(self.settings.daily_trades_warn),
                },
            )

        risk_payload = {
            "client_order_id": client_order_id,
            "symbol": req.symbol,
            "direction": req.direction.value,
            "quantity": req.quantity,
            "order_type": req.order_type.value,
            "price": submit_price,
            "approved": decision.approved,
            "reject_code": decision.reject_code.value if decision.reject_code else None,
            "reject_reason": decision.reject_reason,
        }
        self.db.append_event("RISK_DECISION", client_order_id, risk_payload)

        if not decision.approved:
            self._persist_rejected_order(
                client_order_id=client_order_id,
                req=req,
                price=submit_price,
                reject_code=decision.reject_code or RejectCode.QUOTE_INVALID,
                reject_reason=decision.reject_reason or "Rejected",
            )
            return OrderCreateResponse(
                client_order_id=client_order_id,
                status=OrderStatus.REJECTED,
                reject_code=decision.reject_code,
                reject_reason=decision.reject_reason,
            )

        broker_order_id = f"PAPER-{client_order_id}"
        expires_at = (now + timedelta(seconds=timeout_seconds)).isoformat()
        order_row = {
            "client_order_id": client_order_id,
            "broker_order_id": broker_order_id,
            "signal_id": None,
            "symbol": req.symbol,
            "direction": req.direction.value,
            "order_type": req.order_type.value,
            "quantity": req.quantity,
            "price": submit_price,
            "time_in_force": time_in_force,
            "timeout_seconds": timeout_seconds,
            "status": OrderStatus.NEW.value,
            "expires_at": expires_at,
        }
        self.db.insert_order(order_row)
        self.db.append_event(
            "ORDER_EVENT",
            client_order_id,
            {
                "client_order_id": client_order_id,
                "broker_order_id": broker_order_id,
                "status": "NEW",
                "cum_filled_qty": 0,
            },
        )

        # Attempt immediate match once.
        self._try_match_order(client_order_id, quote)
        updated = self.db.get_order(client_order_id)
        status = OrderStatus(updated["status"]) if updated else OrderStatus.NEW
        return OrderCreateResponse(client_order_id=client_order_id, status=status)

    def cancel_order(self, client_order_id: str) -> OrderStatus:
        return self._cancel_order_internal(client_order_id, reason="Manual cancel")

    def _cancel_order_internal(self, client_order_id: str, reason: str) -> OrderStatus:
        order = self.db.get_order(client_order_id)
        if not order:
            return OrderStatus.REJECTED
        if order["status"] not in ("NEW", "CANCEL_PENDING"):
            return OrderStatus(order["status"])

        self.db.update_order_status(client_order_id, OrderStatus.CANCELED.value)
        self.db.set_order_expires_at(client_order_id, None)
        self.db.append_event(
            "ORDER_EVENT",
            client_order_id,
            {
                "client_order_id": client_order_id,
                "broker_order_id": order.get("broker_order_id"),
                "status": "CANCELED",
                "cum_filled_qty": int(order.get("cum_filled_qty", 0)),
                "reason": reason,
            },
        )
        return OrderStatus.CANCELED

    def _persist_rejected_order(
        self,
        *,
        client_order_id: str,
        req: OrderCreateRequest,
        price: float,
        reject_code: RejectCode,
        reject_reason: str,
    ) -> None:
        row = {
            "client_order_id": client_order_id,
            "broker_order_id": None,
            "signal_id": None,
            "symbol": req.symbol,
            "direction": req.direction.value,
            "order_type": req.order_type.value,
            "quantity": req.quantity,
            "price": price,
            "time_in_force": "GFD",
            "timeout_seconds": 0,
            "status": OrderStatus.REJECTED.value,
            "reject_code": reject_code.value,
            "reject_reason": reject_reason,
            "expires_at": None,
        }
        self.db.insert_order(row)
        self.db.append_event(
            "ORDER_EVENT",
            client_order_id,
            {
                "client_order_id": client_order_id,
                "status": "REJECTED",
                "reject_code": reject_code.value,
                "reject_reason": reject_reason,
            },
        )

    def _try_match_order(self, client_order_id: str, quote: Any) -> None:
        order = self.db.get_order(client_order_id)
        if not order or order["status"] != "NEW":
            return

        last = float(quote.last)
        bid1 = float(quote.bid1 or last)
        ask1 = float(quote.ask1 or last)
        order_price = float(order["price"])

        direction = order["direction"]
        if direction == "BUY":
            crossed = order_price >= ask1
            fill_price = ask1
        else:
            crossed = order_price <= bid1
            fill_price = bid1

        if not crossed:
            return

        parsed = parse_symbol(order["symbol"])
        fill_qty = int(order["quantity"])
        trade_value = fill_price * fill_qty
        fees = calc_fees(trade_value, direction, parsed.market)

        account = self.db.get_account()
        cash = float(account["cash"])
        if direction == "BUY":
            cash -= trade_value + fees.total
        else:
            cash += trade_value - fees.total

        position = self.db.get_position(order["symbol"])
        total_qty = int(position["total_quantity"]) if position else 0
        available_qty = int(position["available_quantity"]) if position else 0
        avg_cost = float(position["avg_cost"]) if position else 0.0

        if direction == "BUY":
            new_total = total_qty + fill_qty
            new_available = available_qty  # T+1
            new_avg = (
                (total_qty * avg_cost + fill_qty * fill_price) / new_total
                if new_total > 0
                else fill_price
            )
        else:
            new_total = total_qty - fill_qty
            new_available = max(0, available_qty - fill_qty)
            new_avg = avg_cost if new_total > 0 else 0.0

        if new_total <= 0:
            self.db.upsert_position(order["symbol"], 0, 0, 0.0)
        else:
            self.db.upsert_position(order["symbol"], new_total, new_available, new_avg)

        # Best-effort total value update without extra quote requests:
        # mark the filled symbol at fill_price, keep others at avg_cost (refresh via /account for true MTM).
        total_value = cash
        for pos in self.db.list_positions():
            qty = int(pos["total_quantity"])
            if qty <= 0:
                continue
            if pos["symbol"] == order["symbol"]:
                total_value += qty * float(fill_price)
            else:
                total_value += qty * float(pos["avg_cost"])
        self.db.update_account(cash=cash, total_value=total_value)

        fill_id = _uuid()
        now = now_cn().isoformat()
        self.db.insert_fill(
            {
                "fill_id": fill_id,
                "client_order_id": client_order_id,
                "broker_trade_id": f"PAPERFILL-{fill_id}",
                "broker_order_id": order.get("broker_order_id"),
                "symbol": order["symbol"],
                "direction": direction,
                "quantity": fill_qty,
                "price": fill_price,
                "commission": fees.commission,
                "stamp_tax": fees.stamp_tax,
                "transfer_fee": fees.transfer_fee,
                "trade_time": now,
            }
        )
        self.db.append_event(
            "TRADE_EVENT",
            client_order_id,
            {
                "fill_id": fill_id,
                "client_order_id": client_order_id,
                "symbol": order["symbol"],
                "direction": direction,
                "qty": fill_qty,
                "price": fill_price,
                "commission": fees.commission,
                "stamp_tax": fees.stamp_tax,
                "transfer_fee": fees.transfer_fee,
                "trade_time": now,
            },
        )

        self.db.update_order_status(client_order_id, OrderStatus.FILLED.value, cum_filled_qty=fill_qty)
        self.db.set_order_expires_at(client_order_id, None)
        self.db.append_event(
            "ORDER_EVENT",
            client_order_id,
            {
                "client_order_id": client_order_id,
                "broker_order_id": order.get("broker_order_id"),
                "status": "FILLED",
                "cum_filled_qty": fill_qty,
            },
        )

    def refresh_account_value(self) -> dict[str, Any]:
        account = self.db.get_account()
        cash = float(account["cash"])
        positions = self.db.list_positions()
        symbols = [p["symbol"] for p in positions if int(p["total_quantity"]) > 0]
        quotes = self.quote_service.fetch_quotes(symbols)

        total_value = cash
        for p in positions:
            qty = int(p["total_quantity"])
            if qty <= 0:
                continue
            q = quotes.get(p["symbol"])
            mark = float(q.last) if q else float(p["avg_cost"])
            total_value += qty * mark

        self.db.update_account(cash=cash, total_value=total_value)
        return self.db.get_account()

    async def background_loop(self) -> None:
        while True:
            try:
                self._process_expired_orders()
                self._process_open_orders_matching()
                self._set_day_start_value_if_needed()
                self._daily_unfreeze_if_needed()
                self._daily_pnl_if_needed()
            except Exception as e:
                self.db.append_event("ENGINE_ERROR", None, {"error": str(e)})
            await asyncio.sleep(float(self.settings.poll_seconds))

    def _process_expired_orders(self) -> None:
        now = now_cn().isoformat()
        for order in self.db.list_expired_open_orders(now):
            self._cancel_order_internal(order["client_order_id"], reason="Timeout")

    def _process_open_orders_matching(self) -> None:
        open_orders = self.db.list_open_orders()
        if not open_orders:
            return
        symbols = [o["symbol"] for o in open_orders]
        quotes = self.quote_service.fetch_quotes(symbols)
        for order in open_orders:
            quote = quotes.get(order["symbol"])
            if quote is None:
                continue
            self._try_match_order(order["client_order_id"], quote)

    def _daily_unfreeze_if_needed(self) -> None:
        now = now_cn()
        if not is_weekday(now):
            return
        if now.time() < datetime.strptime("09:25:00", "%H:%M:%S").time():
            return
        today = now.strftime("%Y-%m-%d")
        last = self.db.get_state("last_unfreeze_date")
        if last == today:
            return
        for pos in self.db.list_positions():
            total_qty = int(pos["total_quantity"])
            if total_qty <= 0:
                continue
            self.db.upsert_position(pos["symbol"], total_qty, total_qty, float(pos["avg_cost"]))
        self.db.set_state("last_unfreeze_date", today)
        self.db.append_event("TPLUS1_UNFREEZE", None, {"date": today})

    def _set_day_start_value_if_needed(self) -> None:
        now = now_cn()
        if not is_weekday(now):
            return
        # Start-of-day snapshot after continuous auction starts.
        if now.time() < datetime.strptime("09:30:00", "%H:%M:%S").time():
            return
        today = now.strftime("%Y-%m-%d")
        if self.db.get_state("day_start_date") == today:
            return
        account = self.refresh_account_value()
        self.db.set_state("day_start_date", today)
        self.db.set_state("day_start_value", str(float(account["total_value"])))
        self.db.append_event("DAY_START_SNAPSHOT", None, {"date": today, "start_value": float(account["total_value"])})

    def _daily_pnl_if_needed(self) -> None:
        now = now_cn()
        if not is_weekday(now):
            return
        # After close auction starts; compute once per day.
        if now.time() < datetime.strptime("15:05:00", "%H:%M:%S").time():
            return
        today = now.strftime("%Y-%m-%d")
        if self.db.get_state("last_daily_pnl_date") == today:
            return
        self.compute_daily_pnl(today)
        self.db.set_state("last_daily_pnl_date", today)

    def compute_daily_pnl(self, date: str) -> None:
        account = self.refresh_account_value()
        end_value = float(account["total_value"])

        start_value_raw = self.db.get_state("day_start_value")
        start_value = float(start_value_raw) if start_value_raw is not None else end_value

        positions = self.db.list_positions()
        symbols = [p["symbol"] for p in positions if int(p["total_quantity"]) > 0]
        quotes = self.quote_service.fetch_quotes(symbols)

        unrealized = 0.0
        for p in positions:
            qty = int(p["total_quantity"])
            if qty <= 0:
                continue
            avg_cost = float(p["avg_cost"])
            q = quotes.get(p["symbol"])
            mark = float(q.last) if q else avg_cost
            unrealized += qty * (mark - avg_cost)

        trades = self.db.count_trades_for_date(date)
        fees = self.db.sum_fees_for_date(date)

        self.db.upsert_daily_pnl(
            date=date,
            start_value=start_value,
            end_value=end_value,
            realized_pnl=0.0,
            unrealized_pnl=unrealized,
            commission=fees,
            trades=trades,
        )
        self.db.append_event(
            "DAILY_PNL",
            None,
            {
                "date": date,
                "start_value": start_value,
                "end_value": end_value,
                "realized_pnl": 0.0,
                "unrealized_pnl": unrealized,
                "commission": fees,
                "trades": trades,
            },
        )
