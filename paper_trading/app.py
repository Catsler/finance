from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from paper_trading.db import PaperTradingDB
from paper_trading.engine import PaperTradingEngine
from paper_trading.candle_service import fetch_60m_candles
from paper_trading.trend_service import calculate_daily_trend
from paper_trading.models import (
    AccountView,
    CancelResponse,
    DailyPnlView,
    EventView,
    FillView,
    KillSwitchRequest,
    KillSwitchView,
    OrderCreateRequest,
    OrderCreateResponse,
    PositionView,
    Quote,
)
from paper_trading.quote_service import QuoteService
from paper_trading.intraday_service import IntradayService
from paper_trading.settings import get_settings



@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = PaperTradingDB(db_path=settings.db_path)
    db.set_initial_cash_if_empty(settings.initial_cash)

    quote_service = QuoteService(quote_cache_seconds=settings.quote_cache_seconds)
    intraday_service = IntradayService()
    engine = PaperTradingEngine(db=db, quote_service=quote_service, settings=settings)

    app.state.settings = settings
    app.state.db = db
    app.state.engine = engine
    app.state.intraday_service = intraday_service

    task = asyncio.create_task(engine.background_loop())
    try:
        yield
    finally:
        task.cancel()
        db.close()


app = FastAPI(title="Paper Trading API (MVP1)", version="0.1.0", lifespan=lifespan)


@app.get("/api/v1/quotes", response_model=list[Quote])
def get_quotes(symbols: Annotated[str, Query(description="Comma-separated symbols, e.g. 000001.SZ,600519.SH")]):
    symbols_list = [s.strip() for s in symbols.split(",") if s.strip()]
    quotes = app.state.engine.quote_service.fetch_quotes(symbols_list)
    return list(quotes.values())


@app.get("/api/v1/candles")
def get_candles(
    symbol: Annotated[str, Query(description="Stock symbol, e.g. 000001.SZ")],
    tf: Annotated[str, Query(description="Timeframe, only '60m' supported in v0.2")] = "60m",
    adjust: Annotated[Literal["front", "none", "back"], Query(description="Adjust type")] = "front",
    limit: Annotated[int, Query(ge=1, le=1000, description="Max candles to return")] = 400,
    include_incomplete: Annotated[bool, Query(description="Include incomplete bar")] = False,
):
    """
    Get 60-minute candles for charting
    
    Returns candles with bar_end_time semantics:
    - candles[].time represents the **end time** of the bar
    - last_complete_time indicates the most recent completed bar
    - By default (include_incomplete=false), only returns completed bars
    """
    if tf != "60m":
        return JSONResponse(
            status_code=400,
            content={"error": f"Only '60m' timeframe is supported in v0.2, got '{tf}'"}
        )
    
    try:
        candles, last_complete_time = fetch_60m_candles(
            symbol=symbol,
            adjust=adjust,
            limit=limit,
        )
        
        return {
            "symbol": symbol,
            "tf": tf,
            "adjust": adjust,
            "last_complete_time": last_complete_time.isoformat() if last_complete_time else None,
            "candles": candles,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/v1/intraday/{symbol}")
def get_intraday(
    symbol: str,
    period: Annotated[str, Query(description="Period: 1, 5, 15, 30, 60 (minutes)")] = '1'
):
    """
    Get intraday minute-level data
    
    Returns minute bars for the current trading day with average price.
    """
    try:
        data = app.state.intraday_service.get_intraday(symbol, period)
        return data
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/v1/trend/daily")
def get_daily_trend(
    symbol: Annotated[str, Query(description="Stock symbol, e.g. 000001.SZ")],
    ma: Annotated[int, Query(ge=5, le=60, description="MA period")] = 20,
    lookback: Annotated[int, Query(ge=1, le=20, description="Lookback days for slope")] = 5,
):
    """
    Get daily trend classification (UP/DOWN/FLAT)
    
    Uses qfq (front-adjusted) data to avoid false breakouts from dividends.
    Trend is determined by MA slope and close vs MA position.
    
    Returns:
        {
            'symbol': str,
            'trend': 'UP' | 'DOWN' | 'FLAT',
            'ma': int,
            'lookback': int,
            'adjust': 'qfq',
            'ma_last': float,
            'close_last': float,
            'slope': float,
            'asof_date': str,  # YYYY-MM-DD
            'close_time': str   # ISO timestamp
        }
    """
    try:
        result = calculate_daily_trend(
            symbol=symbol,
            ma_period=ma,
            lookback=lookback
        )
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/v1/account", response_model=AccountView)
def get_account():
    account = app.state.engine.refresh_account_value()
    return AccountView(
        cash=float(account["cash"]),
        total_value=float(account["total_value"]),
        updated_at=datetime.fromisoformat(account["updated_at"]),
    )


@app.get("/api/v1/positions", response_model=list[PositionView])
def get_positions():
    positions = app.state.db.list_positions()
    out: list[PositionView] = []
    for p in positions:
        out.append(
            PositionView(
                symbol=p["symbol"],
                total_quantity=int(p["total_quantity"]),
                available_quantity=int(p["available_quantity"]),
                avg_cost=float(p["avg_cost"]),
                updated_at=datetime.fromisoformat(p["updated_at"]),
            )
        )
    return out


@app.post("/api/v1/orders", response_model=OrderCreateResponse)
def create_order(req: OrderCreateRequest):
    return app.state.engine.create_order(req)


@app.post("/api/v1/orders/{client_order_id}/cancel", response_model=CancelResponse)
def cancel_order(client_order_id: str):
    status = app.state.engine.cancel_order(client_order_id)
    return CancelResponse(client_order_id=client_order_id, status=status)


@app.get("/api/v1/orders")
def list_orders(
    status: Annotated[str | None, Query(description="Optional status filter, e.g. NEW")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
):
    return {"orders": app.state.db.list_orders(status=status, limit=limit)}


@app.get("/api/v1/fills", response_model=list[FillView])
def list_fills(
    since: Annotated[str | None, Query(description="ISO time, e.g. 2025-12-18T09:30:00")] = None,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
):
    rows = app.state.db.list_fills(since_iso=since, limit=limit)
    out: list[FillView] = []
    for r in rows:
        out.append(
            FillView(
                fill_id=r["fill_id"],
                client_order_id=r["client_order_id"],
                symbol=r["symbol"],
                direction=r["direction"],
                quantity=int(r["quantity"]),
                price=float(r["price"]),
                commission=float(r["commission"]),
                stamp_tax=float(r["stamp_tax"]),
                transfer_fee=float(r["transfer_fee"]),
                trade_time=datetime.fromisoformat(r["trade_time"]),
            )
        )
    return out


@app.get("/api/v1/pnl/daily", response_model=list[DailyPnlView])
def list_daily_pnl(
    date_from: Annotated[str | None, Query(alias="from", description="YYYY-MM-DD")] = None,
    date_to: Annotated[str | None, Query(alias="to", description="YYYY-MM-DD")] = None,
):
    rows = app.state.db.list_daily_pnl(date_from=date_from, date_to=date_to)
    out: list[DailyPnlView] = []
    for r in rows:
        out.append(
            DailyPnlView(
                date=r["date"],
                start_value=r.get("start_value"),
                end_value=r.get("end_value"),
                realized_pnl=r.get("realized_pnl"),
                unrealized_pnl=r.get("unrealized_pnl"),
                commission=r.get("commission"),
                trades=r.get("trades"),
                created_at=datetime.fromisoformat(r["created_at"]),
            )
        )
    return out


@app.get("/api/v1/events", response_model=list[EventView])
def list_events(
    since_id: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
):
    events = app.state.db.list_events(since_id=since_id, limit=limit)
    out: list[EventView] = []
    for e in events:
        out.append(
            EventView(
                id=e["id"],
                event_type=e["event_type"],
                related_id=e["related_id"],
                created_at=datetime.fromisoformat(e["created_at"]),
                payload=e["payload"],
            )
        )
    return out


@app.get("/api/v1/risk/kill_switch", response_model=KillSwitchView)
def get_kill_switch():
    state = app.state.engine.get_kill_switch()
    return KillSwitchView(enabled=state["enabled"], updated_at=datetime.fromisoformat(state["updated_at"]))


@app.post("/api/v1/risk/kill_switch", response_model=KillSwitchView)
def set_kill_switch(req: KillSwitchRequest):
    state = app.state.engine.set_kill_switch(req.enabled)
    return KillSwitchView(enabled=state["enabled"], updated_at=datetime.fromisoformat(state["updated_at"]))


@app.exception_handler(Exception)
def unhandled_exception_handler(request, exc: Exception):
    app.state.db.append_event("UNHANDLED_EXCEPTION", None, {"error": str(exc)})
    return JSONResponse(status_code=500, content={"error": str(exc)})
