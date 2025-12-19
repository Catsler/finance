#!/usr/bin/env python3
"""
MVP2-A: KDJ 60m signal scanner

Outputs:
  - results/pending_signals.json (overwrite)  : signals pending confirmation/execution
  - results/phase7_kdj_signals.jsonl (append): audit log
  - results/phase7_kdj_state.json            : cooldown/dedup/execution counters

Run (Paper server recommended):
  python scripts/kdj_scan.py
  python scripts/kdj_scan.py --symbols 000001.SZ,300750.SZ
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from pathlib import Path as _Path

# Ensure project root is importable when running as a script.
PROJECT_ROOT = _Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import StockPoolConfig
from utils.io import save_json_with_metadata
from utils.kdj_60m_data import Kdj60mDataFetcher, KdjDataError
from utils.kdj_indicators import prepare_60m_indicators, last_completed_bar
from utils.kdj_rules import build_signal, compute_amp_pct_from_quote
from utils.kdj_state import load_state, save_state, should_emit_signal, mark_pending
from utils.paper_api_client import PaperApiClient, PaperApiError
from utils.realtime_quote import get_realtime_quotes


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _cn_now_iso() -> str:
    # Paper backend uses Asia/Shanghai; using local time is fine for MVP.
    return datetime.now().astimezone().isoformat()


def _default_symbols_top5() -> list[str]:
    pool = StockPoolConfig.from_yaml("stock_pool.yaml")
    symbols = pool.get_symbols("small_cap")
    return symbols[:5]


def _try_fetch_quotes(
    *,
    paper_client: PaperApiClient,
    symbols: list[str],
) -> dict[str, dict[str, Any]]:
    try:
        return paper_client.get_quotes(symbols)
    except Exception:
        # Fallback to direct Sina fetch (does not require the server).
        raw = get_realtime_quotes(symbols, cache_seconds=0)
        return {q["symbol"]: q for q in raw if q and q.get("symbol")}


def main() -> int:
    parser = argparse.ArgumentParser(description="KDJ 60m scanner (MVP2-A)")
    parser.add_argument(
        "--symbols",
        default="",
        help="Comma-separated symbols; default is stock_pool.yaml small_cap top5",
    )
    parser.add_argument("--paper-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--out", default="results/pending_signals.json")
    parser.add_argument("--state", default="results/phase7_kdj_state.json")
    parser.add_argument(
        "--log",
        default="",
        help="Audit jsonl path (default: results/phase7_kdj_signals_YYYYMMDD.jsonl)",
    )
    parser.add_argument("--buy-qty", type=int, default=400)
    parser.add_argument("--sell-qty", type=int, default=400)
    parser.add_argument("--cooldown-minutes", type=int, default=60)
    args = parser.parse_args()

    out_path = Path(args.out)
    state_path = Path(args.state)
    now = datetime.now().astimezone()
    today = now.strftime("%Y%m%d")
    log_path = Path(args.log) if args.log else Path(f"results/phase7_kdj_signals_{today}.jsonl")

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()] if args.symbols else _default_symbols_top5()

    today_human = now.strftime("%Y-%m-%d")

    state = load_state(state_path)
    paper = PaperApiClient(base_url=args.paper_url)
    fetcher = Kdj60mDataFetcher(cache_ttl_seconds=3600)

    quotes = _try_fetch_quotes(paper_client=paper, symbols=symbols)

    pending: list[dict[str, Any]] = []

    for symbol in symbols:
        scan_record: dict[str, Any] = {
            "event": "SCAN",
            "timestamp": _cn_now_iso(),
            "date": today_human,
            "symbol": symbol,
        }
        try:
            df = fetcher.fetch(symbol)
            df = prepare_60m_indicators(df)
            bar = last_completed_bar(df)
            if bar is None:
                scan_record["status"] = "SKIP"
                scan_record["reason"] = "no_bars"
                _append_jsonl(log_path, scan_record)
                continue

            bar_end = bar["datetime"]
            bar_end_iso = pd_to_iso(bar_end)

            quote = quotes.get(symbol)
            amp_pct = compute_amp_pct_from_quote(quote) if quote else None

            signals = build_signal(
                symbol=symbol,
                bar_end_time_iso=bar_end_iso,
                j=float(bar.get("j")),
                close_60m=float(bar.get("close")),
                ma20_60m=float(bar.get("ma20")) if not is_nan(bar.get("ma20")) else None,
                amp_pct_today=float(amp_pct) if amp_pct is not None else None,
                buy_qty=int(args.buy_qty),
                sell_qty_suggested=int(args.sell_qty),
            )

            scan_record.update(
                {
                    "bar_end_time": bar_end_iso,
                    "j": float(bar.get("j")),
                    "close_60m": float(bar.get("close")),
                    "ma20_60m": float(bar.get("ma20")) if not is_nan(bar.get("ma20")) else None,
                    "amp_pct_today": float(amp_pct) if amp_pct is not None else None,
                    "signals_found": len(signals),
                }
            )

            for s in signals:
                allowed, reason = should_emit_signal(
                    state, symbol=s.symbol, side=s.direction, dedup_key=s.dedup_key, now=now
                )
                if not allowed:
                    _append_jsonl(
                        log_path,
                        {
                            "event": "SIGNAL_FILTERED",
                            "timestamp": _cn_now_iso(),
                            "date": today_human,
                            "symbol": s.symbol,
                            "direction": s.direction,
                            "bar_end_time": s.bar_end_time,
                            "dedup_key": s.dedup_key,
                            "reason": reason,
                        },
                    )
                    continue

                mark_pending(
                    state,
                    symbol=s.symbol,
                    side=s.direction,
                    dedup_key=s.dedup_key,
                    now=now,
                    cooldown_minutes=int(args.cooldown_minutes),
                )

                pending_item = {
                    "signal_id": f"kdj-{s.dedup_key}",
                    **asdict(s),
                    "dedup_key": s.dedup_key,
                }
                pending.append(pending_item)
                _append_jsonl(
                    log_path,
                    {
                        "event": "SIGNAL_PENDING",
                        "timestamp": _cn_now_iso(),
                        "date": today_human,
                        "symbol": s.symbol,
                        "direction": s.direction,
                        "bar_end_time": s.bar_end_time,
                        "dedup_key": s.dedup_key,
                        "execute_allowed": s.execute_allowed,
                        "skip_reason": s.skip_reason,
                    },
                )

            scan_record["status"] = "OK"
            _append_jsonl(log_path, scan_record)

        except KdjDataError as e:
            scan_record["status"] = "SKIP"
            scan_record["reason"] = f"data_error: {e}"
            _append_jsonl(log_path, scan_record)
            continue
        except Exception as e:
            scan_record["status"] = "ERROR"
            scan_record["reason"] = str(e)
            _append_jsonl(log_path, scan_record)
            continue

    save_state(state_path, state)

    payload = {
        "generated_at": _cn_now_iso(),
        "symbols": symbols,
        "signals": pending,
    }
    save_json_with_metadata(payload, str(out_path), phase="Phase 7 KDJ", version="2.0.0")
    print(f"✓ pending signals: {len(pending)} → {out_path}")
    return 0


def is_nan(v: Any) -> bool:
    try:
        return v != v
    except Exception:
        return False


def pd_to_iso(v: Any) -> str:
    try:
        if hasattr(v, "to_pydatetime"):
            return v.to_pydatetime().astimezone().isoformat()
        return str(v)
    except Exception:
        return str(v)


if __name__ == "__main__":
    raise SystemExit(main())
