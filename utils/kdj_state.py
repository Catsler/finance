from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class KdjState:
    cooldown_until: dict[str, str]  # key: symbol|side -> iso datetime
    last_dedup_key: dict[str, str]  # key: symbol|side -> dedup_key
    daily_exec_count: dict[str, dict[str, int]]  # date -> symbol -> count

    @staticmethod
    def empty() -> "KdjState":
        return KdjState(cooldown_until={}, last_dedup_key={}, daily_exec_count={})

    def to_dict(self) -> dict:
        return {
            "cooldown_until": self.cooldown_until,
            "last_dedup_key": self.last_dedup_key,
            "daily_exec_count": self.daily_exec_count,
        }


def load_state(path: Path) -> KdjState:
    if not path.exists():
        return KdjState.empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return KdjState(
            cooldown_until=dict(data.get("cooldown_until", {})),
            last_dedup_key=dict(data.get("last_dedup_key", {})),
            daily_exec_count=dict(data.get("daily_exec_count", {})),
        )
    except Exception:
        return KdjState.empty()


def save_state(path: Path, state: KdjState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_iso(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def should_emit_signal(state: KdjState, *, symbol: str, side: str, dedup_key: str, now: datetime) -> tuple[bool, str | None]:
    symbol_side = f"{symbol}|{side}"

    if state.last_dedup_key.get(symbol_side) == dedup_key:
        return False, "duplicate_dedup_key"

    cooldown_iso = state.cooldown_until.get(symbol_side)
    if cooldown_iso:
        cooldown_dt = _parse_iso(cooldown_iso)
        if cooldown_dt and now < cooldown_dt:
            return False, "cooldown"

    return True, None


def mark_pending(state: KdjState, *, symbol: str, side: str, dedup_key: str, now: datetime, cooldown_minutes: int = 60) -> None:
    symbol_side = f"{symbol}|{side}"
    state.last_dedup_key[symbol_side] = dedup_key
    state.cooldown_until[symbol_side] = (now + timedelta(minutes=cooldown_minutes)).isoformat()


def can_execute_today(state: KdjState, *, symbol: str, date: str, daily_limit: int = 3) -> bool:
    return int(state.daily_exec_count.get(date, {}).get(symbol, 0)) < daily_limit


def record_execution(state: KdjState, *, symbol: str, date: str) -> None:
    state.daily_exec_count.setdefault(date, {})
    state.daily_exec_count[date][symbol] = int(state.daily_exec_count[date].get(symbol, 0)) + 1

