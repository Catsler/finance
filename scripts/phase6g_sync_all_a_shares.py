#!/usr/bin/env python3
"""
Phase 6G: 同步全量 A 股股票信息（可选下载历史行情）

默认仅同步全市场股票列表（SH/SZ，可选 BJ），输出到 results/。

用法：
  # 仅同步股票列表（推荐先跑这个）
  python3 scripts/phase6g_sync_all_a_shares.py

  # 包含北交所（仅列表；下载阶段目前只支持 .SH/.SZ）
  python3 scripts/phase6g_sync_all_a_shares.py --include-bj

  # 下载历史行情（强烈建议先用 --limit 小规模试跑）
  python3 scripts/phase6g_sync_all_a_shares.py --download-prices --limit 50 --parallel 5

说明：
  - 下载输出位置：~/.qlib/qlib_data/cn_data/*.csv（CSV 存储，不依赖 qlib 包）
  - 复权口径：默认 qfq（Total Return 视角）；可用 --adjust "" 下载真实价格
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# 添加项目根目录到路径（与其他 scripts 保持一致）
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.io import save_json_with_metadata
from utils.universe import UniverseSyncConfig, fetch_a_share_universe
from utils.data_provider import AKShareProvider


def _is_already_downloaded(symbol: str, min_records: int) -> bool:
    csv_path = Path.home() / ".qlib" / "qlib_data" / "cn_data" / f"{symbol}.csv"
    if not csv_path.exists():
        return False
    try:
        df = pd.read_csv(csv_path)
        return len(df) >= min_records
    except Exception:
        return False


def _download_one(
    provider: AKShareProvider,
    symbol: str,
    years: int,
    adjust: str,
) -> Dict[str, Any]:
    start = time.time()
    result = provider.download_to_qlib(symbol=symbol, years=years, adjust=adjust)
    result["elapsed_sec"] = round(time.time() - start, 2)
    return result


def download_prices(
    symbols: List[str],
    *,
    years: int,
    adjust: str,
    parallel: int,
    resume: bool,
    min_records: int,
) -> Dict[str, Any]:
    provider = AKShareProvider()

    to_download: List[str] = []
    skipped: List[str] = []
    for symbol in symbols:
        if resume and _is_already_downloaded(symbol, min_records=min_records):
            skipped.append(symbol)
            continue
        to_download.append(symbol)

    results: List[Dict[str, Any]] = []

    if parallel <= 1:
        for symbol in to_download:
            results.append(_download_one(provider, symbol, years, adjust))
    else:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(_download_one, provider, symbol, years, adjust): symbol
                for symbol in to_download
            }
            for future in as_completed(futures):
                results.append(future.result())

    success = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]

    return {
        "adjust": adjust,
        "years": years,
        "parallel": parallel,
        "resume": resume,
        "min_records": min_records,
        "total_requested": len(symbols),
        "skipped": len(skipped),
        "attempted": len(to_download),
        "success": len(success),
        "failed": len(failed),
        "failed_samples": failed[:20],
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6G: 同步全量A股股票信息")
    parser.add_argument("--include-bj", action="store_true", help="同步北交所股票列表（仅列表）")
    parser.add_argument(
        "--keep-proxy",
        action="store_true",
        help="保留环境变量代理设置（默认会禁用，以避免 AKShare 代理连接失败）",
    )

    parser.add_argument(
        "--output-csv",
        default="results/phase6g_a_share_universe.csv",
        help="股票列表输出 CSV 路径",
    )
    parser.add_argument(
        "--output-json",
        default="results/phase6g_a_share_universe.json",
        help="股票列表输出 JSON 路径（含元数据）",
    )

    parser.add_argument("--download-prices", action="store_true", help="同步历史行情到本地 cn_data")
    parser.add_argument("--years", type=int, default=3, help="回溯年数（默认3年）")
    parser.add_argument(
        "--adjust",
        default="qfq",
        help='复权类型：""=不复权真实价格, qfq=前复权, hfq=后复权（默认qfq）',
    )
    parser.add_argument("--parallel", type=int, default=3, help="下载并发数（默认3）")
    parser.add_argument("--resume", action="store_true", help="跳过已下载且记录数充足的股票")
    parser.add_argument("--min-records", type=int, default=500, help="resume 判定的最小记录数（默认500）")
    parser.add_argument("--limit", type=int, default=0, help="仅处理前N只股票（用于试跑）")

    args = parser.parse_args()

    Path("results").mkdir(parents=True, exist_ok=True)

    # 1) 同步 Universe
    universe_cfg = UniverseSyncConfig(
        include_bj=args.include_bj,
        disable_proxy=not args.keep_proxy,
    )
    universe = fetch_a_share_universe(universe_cfg)

    if args.limit and args.limit > 0:
        universe = universe.head(args.limit).copy()

    universe_csv = Path(args.output_csv)
    universe.to_csv(universe_csv, index=False, encoding="utf-8-sig")

    universe_payload: Dict[str, Any] = {
        "universe": universe.to_dict(orient="records"),
        "summary": {
            "count": int(len(universe)),
            "by_exchange": universe["exchange"].value_counts().to_dict(),
            "by_source": universe["source"].value_counts().to_dict(),
        },
    }
    save_json_with_metadata(
        universe_payload,
        filepath=args.output_json,
        phase="Phase 6G",
        version="1.0.0",
    )

    print(f"✓ 已同步股票列表: {universe_csv}（{len(universe)} 只）")

    # 2) 可选：下载行情（仅 SH/SZ）
    if args.download_prices:
        download_universe = universe[universe["exchange"].isin(["SH", "SZ"])].copy()
        symbols = download_universe["symbol"].tolist()

        report = download_prices(
            symbols,
            years=args.years,
            adjust=args.adjust,
            parallel=max(1, args.parallel),
            resume=args.resume,
            min_records=args.min_records,
        )

        report_path = "results/phase6g_a_share_price_sync_report.json"
        save_json_with_metadata(
            report,
            filepath=report_path,
            phase="Phase 6G",
            version="1.0.0",
        )
        print(f"✓ 已保存下载报告: {report_path}")

        print(
            "下载摘要: "
            f"requested={report['total_requested']} "
            f"skipped={report['skipped']} "
            f"attempted={report['attempted']} "
            f"success={report['success']} "
            f"failed={report['failed']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
