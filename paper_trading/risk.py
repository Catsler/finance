from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from paper_trading.fees import calc_fees
from paper_trading.models import Direction, OrderType, RejectCode
from paper_trading.symbols import ParsedSymbol, SymbolError, parse_symbol, tick_round
from paper_trading.time_utils import is_order_session, now_cn


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reject_code: RejectCode | None = None
    reject_reason: str | None = None


def _get_limit_ratio(parsed: ParsedSymbol) -> float:
    return 0.20 if parsed.board == "CHINEXT" else 0.10


def evaluate_order(
    *,
    symbol: str,
    direction: Direction,
    quantity: int,
    order_type: OrderType,
    price: float,
    quote: dict,
    cash: float,
    available_quantity: int,
    kill_switch: bool,
    order_value_limit: float,
    daily_trades_count: int,
    daily_trades_warn: int,
    daily_trades_reject: int,
    quote_max_age_seconds: int,
    allow_out_of_session: bool = False,
    now: datetime | None = None,
) -> RiskDecision:
    now = now or now_cn()

    if kill_switch:
        return RiskDecision(False, RejectCode.KILL_SWITCH, "Kill switch enabled")

    try:
        parsed = parse_symbol(symbol)
    except SymbolError as e:
        return RiskDecision(False, RejectCode.SYMBOL_NOT_SUPPORTED, str(e))

    if not allow_out_of_session and not is_order_session(now):
        return RiskDecision(False, RejectCode.OUT_OF_SESSION, "Out of order session")

    if quantity <= 0:
        return RiskDecision(False, RejectCode.INVALID_QUANTITY, "quantity must be > 0")

    if direction == Direction.BUY and quantity % 100 != 0:
        return RiskDecision(False, RejectCode.INVALID_QUANTITY, "BUY quantity must be a multiple of 100 shares")

    if direction == Direction.SELL and quantity > available_quantity:
        return RiskDecision(False, RejectCode.INSUFFICIENT_SELLABLE, "Insufficient sellable quantity (T+1)")

    if daily_trades_count > daily_trades_reject:
        return RiskDecision(False, RejectCode.DAILY_TRADE_LIMIT, f"Daily trades limit exceeded ({daily_trades_count})")

    # Quote validation / freshness
    quote_time = quote.get("quote_time")
    if quote_time is None:
        return RiskDecision(False, RejectCode.QUOTE_INVALID, "Quote missing timestamp")
    try:
        age = (now - quote_time).total_seconds()
    except Exception:
        return RiskDecision(False, RejectCode.QUOTE_INVALID, "Quote timestamp invalid")
    if age > quote_max_age_seconds:
        return RiskDecision(False, RejectCode.QUOTE_STALE, f"Quote too old ({age:.1f}s)")

    prev_close = quote.get("prev_close")
    last = quote.get("last")
    bid1 = quote.get("bid1") or last
    ask1 = quote.get("ask1") or last

    if prev_close is None or prev_close <= 0:
        return RiskDecision(False, RejectCode.QUOTE_INVALID, "prev_close missing")
    if last is None or last <= 0 or bid1 is None or ask1 is None:
        return RiskDecision(False, RejectCode.QUOTE_INVALID, "Quote prices missing")

    # Spread check (if bid/ask are equal fallback, it will pass)
    mid = (ask1 + bid1) / 2
    if mid > 0:
        spread_ratio = (ask1 - bid1) / mid
        if spread_ratio > 0.01:
            return RiskDecision(False, RejectCode.SPREAD_TOO_WIDE, f"Spread too wide ({spread_ratio:.2%})")

    # Price deviation / limit-up-down gating
    limit_ratio = _get_limit_ratio(parsed)
    max_deviation = limit_ratio * 0.8
    up_limit = tick_round(prev_close * (1 + limit_ratio))
    down_limit = tick_round(prev_close * (1 - limit_ratio))

    deviation = abs(price / prev_close - 1)
    if deviation > max_deviation:
        return RiskDecision(False, RejectCode.PRICE_DEVIATION, f"Price deviation too high ({deviation:.2%})")

    if direction == Direction.BUY and (last >= up_limit or ask1 >= up_limit):
        return RiskDecision(False, RejectCode.LIMIT_UP_BUY_BLOCKED, "Limit-up, buy blocked")
    if direction == Direction.SELL and (last <= down_limit or bid1 <= down_limit):
        return RiskDecision(False, RejectCode.LIMIT_DOWN_SELL_BLOCKED, "Limit-down, sell blocked")

    order_value = price * quantity
    if order_value > order_value_limit:
        return RiskDecision(False, RejectCode.ORDER_VALUE_LIMIT, f"Order value limit exceeded ({order_value:.2f})")

    if direction == Direction.BUY:
        fees = calc_fees(order_value, direction.value, parsed.market)
        required_cash = order_value + fees.total
        if cash < required_cash:
            return RiskDecision(False, RejectCode.INSUFFICIENT_CASH, "Insufficient cash")

    # Warn threshold is handled as an event (not a reject) in MVP1.
    return RiskDecision(True, None, None)
