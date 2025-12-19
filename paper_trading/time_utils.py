from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo


CN_TZ = ZoneInfo("Asia/Shanghai")


def now_cn() -> datetime:
    return datetime.now(tz=CN_TZ)


@dataclass(frozen=True)
class TradingSession:
    start: time
    end: time  # inclusive end

    def contains(self, dt: datetime) -> bool:
        t = dt.astimezone(CN_TZ).time()
        return self.start <= t <= self.end


ALLOWED_SESSIONS = (
    TradingSession(start=time(9, 30), end=time(11, 30)),
    TradingSession(start=time(13, 0), end=time(14, 57)),
)


def is_order_session(dt: datetime) -> bool:
    return any(s.contains(dt) for s in ALLOWED_SESSIONS)


def parse_quote_timestamp(ts: str) -> datetime | None:
    """
    Parse 'YYYY-MM-DD HH:MM:SS' returned by utils.realtime_quote into aware CN datetime.
    """
    try:
        naive = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return naive.replace(tzinfo=CN_TZ)
    except Exception:
        return None


def is_weekday(dt: datetime) -> bool:
    return dt.astimezone(CN_TZ).weekday() < 5

