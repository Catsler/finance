#!/usr/bin/env python3
"""
MVP2-A: Execute pending KDJ signals against Paper Trading API.

Run:
  python scripts/kdj_execute.py --file results/pending_signals.json --confirm
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pathlib import Path as _Path

# Ensure project root is importable when running as a script.
PROJECT_ROOT = _Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.io import load_json
from utils.kdj_state import load_state, save_state, can_execute_today, record_execution
from utils.paper_api_client import PaperApiClient


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _cn_now() -> datetime:
    return datetime.now().astimezone()


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute pending KDJ signals (MVP2-A)")
    parser.add_argument("--file", default="results/pending_signals.json")
    parser.add_argument("--paper-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--state", default="results/phase7_kdj_state.json")
    parser.add_argument(
        "--log",
        default="",
        help="Audit jsonl path (default: results/phase7_kdj_signals_YYYYMMDD.jsonl)",
    )
    parser.add_argument("--confirm", action="store_true", help="Ask for confirmation before sending orders")
    args = parser.parse_args()

    pending_path = Path(args.file)
    state_path = Path(args.state)
    now = _cn_now()
    today_ymd = now.strftime("%Y%m%d")
    log_path = Path(args.log) if args.log else Path(f"results/phase7_kdj_signals_{today_ymd}.jsonl")

    data, _meta = load_json(str(pending_path))
    signals: list[dict[str, Any]] = list(data.get("signals", []))

    if not signals:
        print("No pending signals.")
        return 0

    today = now.strftime("%Y-%m-%d")

    client = PaperApiClient(base_url=args.paper_url)
    state = load_state(state_path)

    kill = client.get_kill_switch()
    if kill.get("enabled"):
        print("Kill switch is enabled; aborting.")
        return 2

    positions = client.get_positions()

    executable = []
    for s in signals:
        if not s.get("execute_allowed", True):
            _append_jsonl(
                log_path,
                {"event": "EXEC_SKIP", "timestamp": now.isoformat(), "date": today, "reason": "execute_not_allowed", **s},
            )
            continue

        symbol = s["symbol"]
        direction = s["direction"]

        if not can_execute_today(state, symbol=symbol, date=today, daily_limit=3):
            _append_jsonl(
                log_path,
                {"event": "EXEC_SKIP", "timestamp": now.isoformat(), "date": today, "reason": "daily_limit", **s},
            )
            continue

        if direction == "SELL":
            available = int(positions.get(symbol, {}).get("available_quantity", 0))
            qty = min(int(s.get("suggested_quantity", 400)), available)
            if qty <= 0:
                _append_jsonl(
                    log_path,
                    {
                        "event": "EXEC_SKIP",
                        "timestamp": now.isoformat(),
                        "date": today,
                        "reason": "no_sellable",
                        "available_quantity": available,
                        **s,
                    },
                )
                continue
        else:
            qty = int(s.get("suggested_quantity", 400))

        executable.append((s, qty))

    if not executable:
        print("No executable signals after gating.")
        save_state(state_path, state)
        return 0

    if args.confirm:
        print("About to send orders:")
        for s, qty in executable:
            print(f"- {s['symbol']} {s['direction']} {qty} @ AGGRESSIVE (bar_end={s.get('bar_end_time')})")
        ans = input("Type YES to proceed: ").strip()
        if ans != "YES":
            print("Aborted.")
            return 1

    for s, qty in executable:
        symbol = s["symbol"]
        direction = s["direction"]
        order_resp = client.create_order(
            symbol=symbol,
            direction=direction,
            quantity=qty,
            order_type="AGGRESSIVE",
            signal_type="KDJ_60M_T",
        )
        status = order_resp.get("status")
        accepted = status is not None and status != "REJECTED"

        _append_jsonl(
            log_path,
            {
                "event": "EXEC_ORDER",
                "timestamp": _cn_now().isoformat(),
                "date": today,
                "symbol": symbol,
                "direction": direction,
                "quantity": qty,
                "order_response": order_resp,
                "signal": s,
            },
        )

        if accepted:
            record_execution(state, symbol=symbol, date=today)

    save_state(state_path, state)
    print(f"✓ executed: {len(executable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
