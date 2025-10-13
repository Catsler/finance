#!/usr/bin/env python3
"""
最新选股脚本 - 基于最新交易日数据运行选股策略

用法:
    python scripts/select_latest.py --date 2025-10-08
    python scripts/select_latest.py  # 自动检测最新交易日

策略:
    - 20日涨幅 > threshold (默认0%)
    - MA5 > MA10
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# 导入工具
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ruamel.yaml import YAML
    yaml_loader = YAML(typ="safe")
    def load_yaml(path):
        with open(path) as f:
            return yaml_loader.load(f)
except ImportError:
    import yaml
    def load_yaml(path):
        with open(path) as f:
            return yaml.safe_load(f)


def load_stock_pool(yaml_path=Path("stock_pool.yaml"), pool_name="medium_cap"):
    """加载股票池"""
    config = load_yaml(yaml_path)
    stock_pools = config.get("stock_pools", {})

    if pool_name == "medium_cap":
        small_cap = stock_pools.get("small_cap", [])
        medium_conf = stock_pools.get("medium_cap", {})
        additional = medium_conf.get("additional", []) if isinstance(medium_conf, dict) else []
        merged = list(small_cap) + list(additional)
    elif pool_name in stock_pools and isinstance(stock_pools[pool_name], list):
        merged = list(stock_pools[pool_name])
    else:
        raise ValueError(f"未知股票池: {pool_name}")

    stocks = {}
    for item in merged:
        symbol = item.get("symbol") if isinstance(item, dict) else None
        name = item.get("name", symbol) if isinstance(item, dict) else None
        if symbol:
            stocks[symbol] = name or symbol
    return stocks


def load_stock_data(symbol, name, data_dir=Path.home() / ".qlib/qlib_data/cn_data"):
    """
    加载单只股票数据并计算指标

    Returns:
        dict or None: 包含close, ma5, ma10的最新数据
    """
    csv_path = data_dir / f"{symbol}.csv"
    if not csv_path.exists():
        print(f"⚠️ 文件不存在: {csv_path}")
        return None

    df = pd.read_csv(csv_path, parse_dates=["date"], index_col="date")
    df = df.sort_index()

    if df.empty:
        print(f"⚠️ {symbol} 数据为空")
        return None

    # 计算MA
    df["ma5"] = df["close"].rolling(window=5).mean()
    df["ma10"] = df["close"].rolling(window=10).mean()

    # 获取最后一条完整数据
    latest_idx = -1
    while abs(latest_idx) <= len(df):
        latest_row = df.iloc[latest_idx]
        if pd.notna(latest_row["ma5"]) and pd.notna(latest_row["ma10"]):
            break
        latest_idx -= 1
    else:
        print(f"⚠️ {symbol} 无完整MA数据")
        return None

    latest_date = df.index[latest_idx]

    # 计算20日涨幅
    loc = df.index.get_loc(latest_date)
    if loc < 20:
        return_20d = np.nan
    else:
        current_price = df.iloc[loc]["close"]
        price_20d_ago = df.iloc[loc - 20]["close"]
        return_20d = (current_price - price_20d_ago) / price_20d_ago if price_20d_ago > 0 else np.nan

    return {
        "symbol": symbol,
        "name": name,
        "date": latest_date.strftime("%Y-%m-%d"),
        "close": float(df.iloc[latest_idx]["close"]),
        "ma5": float(df.iloc[latest_idx]["ma5"]),
        "ma10": float(df.iloc[latest_idx]["ma10"]),
        "return_20d": float(return_20d) if pd.notna(return_20d) else None,
    }


def check_conditions(data, momentum_threshold=0.0):
    """
    检查是否满足选股条件

    Args:
        data: 股票数据字典
        momentum_threshold: 20日涨幅阈值（百分比）

    Returns:
        bool: 是否满足条件
    """
    if data["return_20d"] is None:
        return False

    # 条件1: 20日涨幅 > threshold
    if data["return_20d"] <= momentum_threshold / 100:
        return False

    # 条件2: MA5 > MA10
    if data["ma5"] <= data["ma10"]:
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="最新选股脚本")
    parser.add_argument("--date", help="指定日期 (YYYY-MM-DD)，留空则自动检测最新")
    parser.add_argument("--pool", default="medium_cap", help="股票池名称（默认medium_cap）")
    parser.add_argument("--momentum-threshold", type=float, default=0.0, help="20日涨幅阈值（百分比，默认0.0）")
    parser.add_argument("--output", help="输出JSON文件路径（默认results/latest_selection_YYYYMMDD.json）")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("最新选股系统 - Phase 6E策略")
    print("="*60)

    # 加载股票池
    stocks = load_stock_pool(pool_name=args.pool)
    print(f"✓ 加载股票池: {args.pool} ({len(stocks)}只)")

    # 收集所有股票数据
    all_data = []
    latest_common_date = None

    for symbol, name in stocks.items():
        data = load_stock_data(symbol, name)
        if data:
            all_data.append(data)
            # 记录最新共同日期
            if latest_common_date is None or data["date"] < latest_common_date:
                latest_common_date = data["date"]

    if not all_data:
        print("❌ 未能加载任何股票数据")
        sys.exit(1)

    print(f"✓ 加载 {len(all_data)}/{len(stocks)} 只股票数据")
    print(f"✓ 最新共同交易日: {latest_common_date}")

    # 使用指定日期或最新共同日期
    selection_date = args.date if args.date else latest_common_date
    print(f"\n选股日期: {selection_date}")
    print(f"策略参数: 20日涨幅>{args.momentum_threshold}%, MA5>MA10")
    print("-" * 60)

    # 筛选符合条件的股票
    selected = []
    rejected = []

    for data in all_data:
        if data["date"] != selection_date:
            continue  # 跳过日期不匹配的数据

        is_qualified = check_conditions(data, args.momentum_threshold)

        if is_qualified:
            selected.append(data)
            print(f"✅ {data['symbol']} {data['name']:6s} | 涨幅:{data['return_20d']*100:>6.2f}% | MA5:{data['ma5']:.2f} > MA10:{data['ma10']:.2f}")
        else:
            rejected.append(data)
            reason = []
            if data["return_20d"] is None:
                reason.append("无20日数据")
            elif data["return_20d"] <= args.momentum_threshold / 100:
                reason.append(f"涨幅{data['return_20d']*100:.2f}%≤{args.momentum_threshold}%")
            if data["ma5"] <= data["ma10"]:
                reason.append(f"MA5({data['ma5']:.2f})≤MA10({data['ma10']:.2f})")
            print(f"❌ {data['symbol']} {data['name']:6s} | {', '.join(reason)}")

    print("-" * 60)
    print(f"筛选结果: {len(selected)}/{len(all_data)} 只股票符合条件")

    # 构建输出
    result = {
        "selection_date": selection_date,
        "pool_name": args.pool,
        "pool_size": len(stocks),
        "data_available": len(all_data),
        "selected_count": len(selected),
        "momentum_threshold": args.momentum_threshold,
        "selected_stocks": [s["symbol"] for s in selected],
        "details": {s["symbol"]: s for s in selected},
        "rejected_stocks": [r["symbol"] for r in rejected],
        "rejected_details": {r["symbol"]: r for r in rejected},
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 保存JSON
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = selection_date.replace("-", "")
        output_path = Path(f"results/latest_selection_{date_str}.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 选股结果已保存: {output_path}")

    # 打印摘要
    if selected:
        print("\n" + "="*60)
        print("📊 符合条件的股票（建议持仓）:")
        print("="*60)
        for s in selected:
            print(f"  {s['symbol']}\t{s['name']:8s}\t涨幅:{s['return_20d']*100:>6.2f}%\t收盘:{s['close']:.2f}")
        print("="*60)
    else:
        print("\n⚠️ 当前无股票符合选股条件，建议空仓观望")


if __name__ == "__main__":
    main()
