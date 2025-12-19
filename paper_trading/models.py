from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    AGGRESSIVE = "AGGRESSIVE"
    LIMIT = "LIMIT"


class TimeInForce(str, Enum):
    IOC = "IOC"
    GFD = "GFD"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    SUBMITTED = "SUBMITTED"
    NEW = "NEW"
    FILLED = "FILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELED = "CANCELED"


class RejectCode(str, Enum):
    KILL_SWITCH = "KILL_SWITCH"
    OUT_OF_SESSION = "OUT_OF_SESSION"
    QUOTE_STALE = "QUOTE_STALE"
    QUOTE_INVALID = "QUOTE_INVALID"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    INSUFFICIENT_CASH = "INSUFFICIENT_CASH"
    INSUFFICIENT_SELLABLE = "INSUFFICIENT_SELLABLE"
    PRICE_DEVIATION = "PRICE_DEVIATION"
    LIMIT_UP_BUY_BLOCKED = "LIMIT_UP_BUY_BLOCKED"
    LIMIT_DOWN_SELL_BLOCKED = "LIMIT_DOWN_SELL_BLOCKED"
    SPREAD_TOO_WIDE = "SPREAD_TOO_WIDE"
    ORDER_VALUE_LIMIT = "ORDER_VALUE_LIMIT"
    DAILY_TRADE_LIMIT = "DAILY_TRADE_LIMIT"
    SYMBOL_NOT_SUPPORTED = "SYMBOL_NOT_SUPPORTED"


class Quote(BaseModel):
    symbol: str
    name: str | None = None
    last: float = Field(alias="price")
    open: float | None = None
    high: float | None = None
    low: float | None = None
    bid1: float | None = None
    ask1: float | None = None
    bid1_volume: int | None = None
    ask1_volume: int | None = None
    prev_close: float | None = None
    change_pct: float | None = None
    volume: int | None = None
    amount: float | None = None
    quote_time: datetime | None = None
    source: str | None = None
    tradable: bool = True


class OrderCreateRequest(BaseModel):
    symbol: str
    direction: Direction
    quantity: int = Field(gt=0)
    order_type: OrderType
    limit_price: float | None = Field(default=None, gt=0)
    signal_type: str | None = None


class OrderCreateResponse(BaseModel):
    client_order_id: str
    status: OrderStatus
    reject_code: RejectCode | None = None
    reject_reason: str | None = None


class CancelResponse(BaseModel):
    client_order_id: str
    status: OrderStatus


class AccountView(BaseModel):
    cash: float
    total_value: float
    updated_at: datetime


class PositionView(BaseModel):
    symbol: str
    total_quantity: int
    available_quantity: int
    avg_cost: float
    updated_at: datetime


class FillView(BaseModel):
    fill_id: str
    client_order_id: str
    symbol: str
    direction: Direction
    quantity: int
    price: float
    commission: float
    stamp_tax: float
    transfer_fee: float
    trade_time: datetime


class DailyPnlView(BaseModel):
    date: str
    start_value: float | None = None
    end_value: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None
    commission: float | None = None
    trades: int | None = None
    created_at: datetime


class EventView(BaseModel):
    id: int
    event_type: str
    related_id: str | None = None
    created_at: datetime
    payload: dict[str, Any]


class KillSwitchRequest(BaseModel):
    enabled: bool


class KillSwitchView(BaseModel):
    enabled: bool
    updated_at: datetime
