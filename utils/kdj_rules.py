from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Any


@dataclass(frozen=True)
class KdjSignal:
    symbol: str
    direction: str  # BUY/SELL
    bar_end_time: str  # ISO string
    j: float
    close_60m: float
    ma20_60m: float
    amp_pct_today: float
    suggested_quantity: int
    execute_allowed: bool
    skip_reason: str | None

    @property
    def dedup_key(self) -> str:
        return f"{self.symbol}|{self.direction}|{self.bar_end_time}"


def _parse_iso(dt_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def is_1500_bar(bar_end_time_iso: str) -> bool:
    dt = _parse_iso(bar_end_time_iso)
    if dt is None:
        return False
    t = dt.time()
    return t.hour == 15 and t.minute == 0


def compute_amp_pct_from_quote(quote: dict[str, Any]) -> float | None:
    high = quote.get("high")
    low = quote.get("low")
    prev_close = quote.get("prev_close")
    if high is None or low is None or prev_close is None:
        return None
    if prev_close <= 0:
        return None
    return (float(high) - float(low)) / float(prev_close)


def build_signal(
    *,
    symbol: str,
    bar_end_time_iso: str,
    j: float,
    close_60m: float,
    ma20_60m: float | None,
    amp_pct_today: float | None,
    buy_qty: int,
    sell_qty_suggested: int,
) -> list[KdjSignal]:
    if ma20_60m is None or amp_pct_today is None:
        return []

    signals: list[KdjSignal] = []

    # BUY rule
    if j < 25 and amp_pct_today > 0.02 and close_60m < ma20_60m:
        execute_allowed = not is_1500_bar(bar_end_time_iso)
        signals.append(
            KdjSignal(
                symbol=symbol,
                direction="BUY",
                bar_end_time=bar_end_time_iso,
                j=float(j),
                close_60m=float(close_60m),
                ma20_60m=float(ma20_60m),
                amp_pct_today=float(amp_pct_today),
                suggested_quantity=buy_qty,
                execute_allowed=execute_allowed,
                skip_reason="15:00 bar (no execution)" if not execute_allowed else None,
            )
        )

    # SELL rule
    if j > 75 and amp_pct_today > 0.02 and close_60m > ma20_60m:
        execute_allowed = not is_1500_bar(bar_end_time_iso)
        signals.append(
            KdjSignal(
                symbol=symbol,
                direction="SELL",
                bar_end_time=bar_end_time_iso,
                j=float(j),
                close_60m=float(close_60m),
                ma20_60m=float(ma20_60m),
                amp_pct_today=float(amp_pct_today),
                suggested_quantity=sell_qty_suggested,
                execute_allowed=execute_allowed,
                skip_reason="15:00 bar (no execution)" if not execute_allowed else None,
            )
        )

    return signals

