#!/usr/bin/env python3
"""Phase 6F: 换手率优化实验脚本

特性：
    - 默认评估 2005-01-01 ~ 2024-12-31 的长期表现
    - 同时产出 Baseline(月度调仓) 与三种实验方案的对比
    - 支持单年度快速验证 (--year 2023)
    - 输出 JSON 摘要、Markdown 对比、持仓记录 CSV

实验方案：
    - turnover_reduction: 将调仓频率降至季度，验证换手率与收益权衡
    - stability_filter: 月度调仓 + 波动率过滤，剔除高波动标的
    - combined: 同时应用季度调仓与波动率过滤
"""

from __future__ import annotations

import argparse
import logging
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import pandas as pd

# 允许导入 utils
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.io import ensure_directories, load_benchmark_data, save_json_with_metadata  # noqa: E402

try:
    from ruamel.yaml import YAML  # type: ignore

    def _load_yaml(path: Path) -> dict:
        loader = YAML(typ="safe")
        with path.open(encoding="utf-8") as f:
            return loader.load(f)
except ImportError:  # pragma: no cover - fallback
    import yaml  # type: ignore

    def _load_yaml(path: Path) -> dict:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)


DEFAULT_START = "2005-01-01"
DEFAULT_END = "2024-12-31"
MOMENTUM_WINDOW = 20
STABILITY_WINDOW = 60
TARGET_COUNT = 20
INITIAL_CAPITAL = 1_000_000.0

# 模块级logger（不配置，避免导入副作用）
logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    label: str
    final_value: float
    total_return: float
    annual_return: float
    max_drawdown: float
    avg_turnover: float
    rebalance_count: int
    holdings: List[dict]
    equity_curve: List[dict]

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "final_value": self.final_value,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "avg_turnover": self.avg_turnover,
            "rebalance_count": self.rebalance_count,
        }


def load_stock_pool(pool_name: str = "medium_cap", config_path: Path = Path("stock_pool.yaml")) -> Dict[str, str]:
    if not config_path.exists():
        raise FileNotFoundError(f"股票池配置不存在: {config_path}")

    config = _load_yaml(config_path)
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
        if not symbol:
            continue
        stocks[symbol] = name or symbol
    return stocks


def load_stock_data(symbols: Dict[str, str], start_date: pd.Timestamp, end_date: pd.Timestamp, buffer_days: int = 120) -> Dict[str, pd.DataFrame]:
    data_dir = Path.home() / ".qlib/qlib_data/cn_data"
    fetch_start = start_date - pd.Timedelta(days=buffer_days)

    stock_data: Dict[str, pd.DataFrame] = {}
    for symbol, name in symbols.items():
        csv_path = data_dir / f"{symbol}.csv"
        if not csv_path.exists():
            print(f"❌ 缺少数据文件: {csv_path}")
            continue

        df = pd.read_csv(csv_path, parse_dates=["date"], index_col="date")
        df = df.sort_index()
        filtered = df[(df.index >= fetch_start) & (df.index <= end_date)].copy()
        if filtered.empty:
            print(f"⚠️ {symbol} 在 {start_date.date()} ~ {end_date.date()} 无数据")
            continue

        filtered["symbol"] = symbol
        filtered["name"] = name
        filtered["ma5"] = filtered["close"].rolling(window=5).mean()
        filtered["ma10"] = filtered["close"].rolling(window=10).mean()
        stock_data[symbol] = filtered

    if len(stock_data) < 5:
        raise RuntimeError("可用股票不足 5 只，无法完成回测，请先补齐数据。")

    print(f"✓ 加载 {len(stock_data)} 只股票数据")
    return stock_data


def collect_available_dates(stock_data: Dict[str, pd.DataFrame]) -> List[pd.Timestamp]:
    dates: Set[pd.Timestamp] = set()
    for df in stock_data.values():
        dates.update(df.index)
    if not dates:
        raise RuntimeError("未收集到任何交易日期")
    return sorted(dates)


def align_time_window(available_dates: Sequence[pd.Timestamp], start: pd.Timestamp, end: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    if start >= end:
        raise ValueError("起始日期必须早于结束日期")

    start_idx = bisect_left(available_dates, start)
    if start_idx >= len(available_dates):
        raise ValueError("找不到起始日期之后的交易日")
    start_aligned = available_dates[start_idx]

    end_idx = bisect_right(available_dates, end) - 1
    if end_idx < 0:
        raise ValueError("找不到结束日期之前的交易日")
    end_aligned = available_dates[end_idx]

    if start_aligned >= end_aligned:
        raise ValueError("有效交易区间不足")

    return start_aligned, end_aligned


def generate_rebalance_dates(start: pd.Timestamp, end: pd.Timestamp, freq: str, available_dates: Sequence[pd.Timestamp]) -> List[pd.Timestamp]:
    if freq not in {"monthly", "quarterly"}:
        raise ValueError("freq 仅支持 'monthly' 或 'quarterly'")

    pandas_freq = "M" if freq == "monthly" else "Q"
    raw_dates = pd.date_range(start=start, end=end, freq=pandas_freq)

    aligned: List[pd.Timestamp] = []
    for dt in raw_dates:
        idx = bisect_right(available_dates, dt) - 1
        if idx < 0:
            continue
        candidate = available_dates[idx]
        if candidate < start:
            continue
        if aligned and candidate == aligned[-1]:
            continue
        aligned.append(candidate)

    if not aligned:
        raise RuntimeError("无法生成调仓日期，请检查数据覆盖范围")

    return aligned


def get_price_on_or_before(df: pd.DataFrame, date: pd.Timestamp) -> Tuple[pd.Timestamp, float]:
    idx = df.index.searchsorted(date)
    if idx < len(df.index) and df.index[idx] == date:
        actual_idx = idx
    else:
        actual_idx = idx - 1
    if actual_idx < 0:
        raise KeyError("无可用价格")
    actual_date = df.index[actual_idx]
    return actual_date, float(df.iloc[actual_idx]["close"])


def compute_momentum(df: pd.DataFrame, date: pd.Timestamp, window: int = MOMENTUM_WINDOW) -> float:
    try:
        loc = df.index.get_loc(date)
        if isinstance(loc, slice):
            loc = loc.stop - 1
    except KeyError:
        return float("nan")

    if loc < window:
        return float("nan")

    current_price = df.iloc[loc]["close"]
    past_price = df.iloc[loc - window]["close"]
    if past_price <= 0:
        return float("nan")
    return (current_price - past_price) / past_price


def _annual_volatility(
    df: pd.DataFrame,
    date: pd.Timestamp,
    window: int = 120
) -> Optional[float]:
    """
    计算年化波动率
    
    Args:
        df: 股票数据DataFrame（需包含close列和日期索引）
        date: 计算日期
        window: 回看窗口天数（交易日数量，默认120天）
    
    Returns:
        年化波动率（0.0-1.0范围），计算失败返回None
        
    Note:
        使用DEBUG级别日志记录失败原因，避免CLI噪声
    """
    try:
        loc = df.index.get_loc(date)
        if isinstance(loc, slice):
            loc = loc.stop - 1
    except KeyError:
        logger.debug(f"日期 {date.strftime('%Y-%m-%d')} 不在数据范围内")
        return None

    if loc + 1 < window:
        logger.debug(f"数据不足 {window} 天（当前仅 {loc + 1} 天）")
        return None

    segment = df.iloc[loc - window + 1 : loc + 1]["close"].pct_change().dropna()
    if segment.empty:
        logger.debug(f"收益率序列为空（日期: {date.strftime('%Y-%m-%d')}）")
        return None

    annual_vol = segment.std() * np.sqrt(252)
    if not np.isfinite(annual_vol):
        logger.debug(f"波动率计算结果无效: {annual_vol}（日期: {date.strftime('%Y-%m-%d')}）")
        return None
    
    return annual_vol


def passes_volatility_filter(df: pd.DataFrame, date: pd.Timestamp, threshold: float, window: int = STABILITY_WINDOW) -> bool:
    """
    检查股票是否通过波动率过滤（低波动）
    
    Args:
        df: 股票数据DataFrame
        date: 检查日期
        threshold: 波动率阈值（年化）
        window: 计算窗口（默认使用STABILITY_WINDOW=60天）
    
    Returns:
        True表示波动率≤阈值（通过筛选），False表示高波动或计算失败
    """
    vol = _annual_volatility(df, date, window)
    return vol is not None and vol <= threshold


def select_universe(
    stock_data: Dict[str, pd.DataFrame],
    date: pd.Timestamp,
    momentum_threshold: float,
    target_count: int,
    volatility_threshold: Optional[float] = None,
) -> List[str]:
    threshold_decimal = momentum_threshold / 100.0
    candidates: List[Tuple[str, float]] = []

    for symbol, df in stock_data.items():
        if date not in df.index:
            continue
        momentum = compute_momentum(df, date)
        if not np.isfinite(momentum) or momentum <= threshold_decimal:
            continue
        if volatility_threshold is not None and not passes_volatility_filter(df, date, volatility_threshold):
            continue
        candidates.append((symbol, momentum))

    candidates.sort(key=lambda item: item[1], reverse=True)
    return [symbol for symbol, _ in candidates[:target_count]]


def simulate_period(
    stock_data: Dict[str, pd.DataFrame],
    holdings: Sequence[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
    capital: float,
) -> float:
    if not holdings:
        return capital

    capital_per_stock = capital / len(holdings)
    total_value = 0.0

    for symbol in holdings:
        df = stock_data[symbol]
        try:
            buy_date, buy_price = get_price_on_or_before(df, start)
        except KeyError:
            total_value += capital_per_stock
            continue
        if buy_date != start or buy_price <= 0:
            total_value += capital_per_stock
            continue

        try:
            sell_date, sell_price = get_price_on_or_before(df, end)
        except KeyError:
            total_value += capital_per_stock
            continue
        if sell_date < buy_date or sell_price <= 0:
            total_value += capital_per_stock
            continue

        shares = capital_per_stock / buy_price
        total_value += shares * sell_price

    return total_value


def max_drawdown(values: Sequence[float]) -> float:
    arr = np.array(values, dtype=float)
    if arr.size == 0:
        return 0.0
    cumulative_max = np.maximum.accumulate(arr)
    drawdowns = (arr - cumulative_max) / cumulative_max
    return float(drawdowns.min())


def run_backtest(
    label: str,
    stock_data: Dict[str, pd.DataFrame],
    rebalance_dates: Sequence[pd.Timestamp],
    end_date: pd.Timestamp,
    momentum_threshold: float,
    commission: float,
    target_count: int,
    volatility_threshold: Optional[float] = None,
) -> BacktestResult:
    current_capital = INITIAL_CAPITAL
    holdings_history: List[dict] = []
    turnover_rates: List[float] = []
    equity_dates: List[pd.Timestamp] = [rebalance_dates[0]]
    equity_values: List[float] = [current_capital]

    previous_holdings: List[str] = []

    for idx, date in enumerate(rebalance_dates):
        holdings = select_universe(
            stock_data,
            date,
            momentum_threshold=momentum_threshold,
            target_count=target_count,
            volatility_threshold=volatility_threshold,
        )

        holdings_history.append({
            "date": date.strftime("%Y-%m-%d"),
            "symbols": holdings,
        })

        if not holdings:
            equity_dates.append(date)
            equity_values.append(current_capital)
            previous_holdings = []
            continue

        if idx == 0 and commission > 0:
            current_capital -= current_capital * commission

        if idx > 0:
            prev_set = set(previous_holdings)
            curr_set = set(holdings)
            if prev_set:
                turnover = len(prev_set.symmetric_difference(curr_set)) / len(prev_set)
            else:
                turnover = 1.0
            turnover_rates.append(turnover)
            if commission > 0 and turnover > 0:
                capital_per_stock = current_capital / max(len(curr_set), 1)
                trade_cost = len(prev_set.symmetric_difference(curr_set)) * capital_per_stock * commission
                current_capital -= trade_cost
        previous_holdings = holdings

        next_date = rebalance_dates[idx + 1] if idx + 1 < len(rebalance_dates) else end_date
        current_capital = simulate_period(stock_data, holdings, date, next_date, current_capital)
        equity_dates.append(next_date)
        equity_values.append(current_capital)

    total_return = current_capital / INITIAL_CAPITAL - 1.0
    start_date = rebalance_dates[0]
    total_days = max((end_date - start_date).days, 1)
    annual_return = (1 + total_return) ** (365 / total_days) - 1
    drawdown = max_drawdown(equity_values)
    avg_turnover = float(np.mean(turnover_rates)) if turnover_rates else 0.0

    equity_curve = [
        {"date": dt.strftime("%Y-%m-%d"), "value": val}
        for dt, val in zip(equity_dates, equity_values)
    ]

    return BacktestResult(
        label=label,
        final_value=current_capital,
        total_return=total_return,
        annual_return=annual_return,
        max_drawdown=drawdown,
        avg_turnover=avg_turnover,
        rebalance_count=len(rebalance_dates),
        holdings=holdings_history,
        equity_curve=equity_curve,
    )


def calculate_benchmark_return(benchmark_df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> float:
    df = benchmark_df.copy()
    df = df[(df["date"] >= start) & (df["date"] <= end)]
    if df.empty:
        return 0.0
    start_price = df.iloc[0]["close"]
    end_price = df.iloc[-1]["close"]
    if start_price <= 0:
        return 0.0
    return (end_price - start_price) / start_price


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def validate_phase6f(
    baseline_result: BacktestResult,
    variant_result: BacktestResult,
    benchmark_return: float,
) -> None:
    """
    Phase 6F 实验结果验证和输出

    负责打印实验结果摘要，未来可扩展为：
    - 阈值检查（如收益率/换手率边界）
    - 异常检测（如极端波动、数据质量）
    - 统计显著性检验

    Args:
        baseline_result: 基准策略回测结果
        variant_result: 实验方案回测结果
        benchmark_return: 沪深300基准收益率
    """
    print("\n=== 实验完成 ===")
    print(f"Baseline 总收益: {format_percent(baseline_result.total_return)}")
    print(f"Variant 总收益: {format_percent(variant_result.total_return)}")
    print(f"超额收益(实验-基准): {format_percent(variant_result.total_return - benchmark_return)}")
    
    # 未来扩展点：
    # - 验证收益率在合理范围内（如 -100% ~ +1000%）
    # - 验证换手率异常（如 >200%）
    # - 验证最大回撤异常（如 <-80%）


def generate_markdown(
    window: Tuple[pd.Timestamp, pd.Timestamp],
    baseline: BacktestResult,
    variant: BacktestResult,
    benchmark_return: float,
    output_path: Path,
) -> None:
    start, end = window
    lines = [
        f"# Phase 6F - {variant.label} 实验报告",
        "",
        f"> 时间范围: {start.date()} ~ {end.date()}",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 核心对比",
        "",
        "| 指标 | Baseline(月度) | 实验方案 | 差异 |",
        "|------|----------------|----------|------|",
        f"| 最终收益 | {format_percent(baseline.total_return)} | {format_percent(variant.total_return)} | {format_percent(variant.total_return - baseline.total_return)} |",
        f"| 年化收益 | {format_percent(baseline.annual_return)} | {format_percent(variant.annual_return)} | {format_percent(variant.annual_return - baseline.annual_return)} |",
        f"| 最大回撤 | {format_percent(baseline.max_drawdown)} | {format_percent(variant.max_drawdown)} | {format_percent(variant.max_drawdown - baseline.max_drawdown)} |",
        f"| 平均换手 | {format_percent(baseline.avg_turnover)} | {format_percent(variant.avg_turnover)} | {format_percent(variant.avg_turnover - baseline.avg_turnover)} |",
        f"| 调仓次数 | {baseline.rebalance_count} | {variant.rebalance_count} | {variant.rebalance_count - baseline.rebalance_count:+d} |",
        "",
        "## 基准表现",
        "",
        f"- 沪深300 总收益: {format_percent(benchmark_return)}",
        f"- 实验方案相对基准超额: {format_percent(variant.total_return - benchmark_return)}",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Markdown 报告已生成: {output_path}")


def save_holdings_csv(result: BacktestResult, path: Path) -> None:
    rows = []
    for item in result.holdings:
        rows.append({
            "date": item["date"],
            "symbols": ",".join(item["symbols"]),
            "count": len(item["symbols"]),
        })
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"✓ 持仓记录已保存: {path}")


def determine_window(args: argparse.Namespace) -> Tuple[pd.Timestamp, pd.Timestamp]:
    if args.year:
        start = pd.Timestamp(f"{args.year}-01-01")
        end = pd.Timestamp(f"{args.year}-12-31")
    else:
        start = pd.Timestamp(args.start_date or DEFAULT_START)
        end = pd.Timestamp(args.end_date or DEFAULT_END)
    return start, end


def main() -> None:
    # 配置日志（仅CLI执行时生效，避免污染导入环境）
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    parser = argparse.ArgumentParser(description="Phase 6F 换手率优化实验")
    parser.add_argument("--test", choices=["turnover_reduction", "stability_filter", "combined"], default="turnover_reduction", help="实验方案选择")
    parser.add_argument("--year", type=int, help="指定单一年份测试，例如 2023")
    parser.add_argument("--start-date", dest="start_date", help="自定义起始日期，默认为2005-01-01")
    parser.add_argument("--end-date", dest="end_date", help="自定义结束日期，默认为2024-12-31")
    parser.add_argument("--momentum-threshold", type=float, default=0.0, help="20日涨幅阈值（百分比）")
    parser.add_argument("--stability-threshold", type=float, default=0.15, help="波动率过滤阈值（年化，默认0.15）")
    parser.add_argument("--commission", type=float, default=0.001, help="单边佣金率，例如0.001=0.1%%")
    parser.add_argument("--target-count", type=int, default=TARGET_COUNT, help="目标持仓数量，默认20")
    parser.add_argument("--pool", default="medium_cap", help="股票池名称，默认medium_cap")
    args = parser.parse_args()

    ensure_directories()

    start_hint, end_hint = determine_window(args)
    print(f"实验窗口: {start_hint.date()} ~ {end_hint.date()}")

    symbols = load_stock_pool(args.pool)
    stock_data = load_stock_data(symbols, start_hint, end_hint)
    available_dates = collect_available_dates(stock_data)
    start_aligned, end_aligned = align_time_window(available_dates, start_hint, end_hint)

    baseline_rebalances = generate_rebalance_dates(start_aligned, end_aligned, "monthly", available_dates)

    if args.test == "turnover_reduction":
        variant_label = "Quarterly Rebalance"
        variant_rebalances = generate_rebalance_dates(start_aligned, end_aligned, "quarterly", available_dates)
        volatility_threshold: Optional[float] = None
    elif args.test == "stability_filter":
        variant_label = "Stability Filter"
        variant_rebalances = baseline_rebalances
        volatility_threshold = args.stability_threshold
    else:
        variant_label = "Quarterly + Stability"
        variant_rebalances = generate_rebalance_dates(start_aligned, end_aligned, "quarterly", available_dates)
        volatility_threshold = args.stability_threshold

    print(f"Baseline 调仓次数: {len(baseline_rebalances)}")
    print(f"Variant ({variant_label}) 调仓次数: {len(variant_rebalances)}")

    baseline_result = run_backtest(
        label="Baseline",
        stock_data=stock_data,
        rebalance_dates=baseline_rebalances,
        end_date=end_aligned,
        momentum_threshold=args.momentum_threshold,
        commission=args.commission,
        target_count=args.target_count,
        volatility_threshold=None,
    )

    variant_result = run_backtest(
        label=variant_label,
        stock_data=stock_data,
        rebalance_dates=variant_rebalances,
        end_date=end_aligned,
        momentum_threshold=args.momentum_threshold,
        commission=args.commission,
        target_count=args.target_count,
        volatility_threshold=volatility_threshold,
    )

    benchmark_df = load_benchmark_data(start_aligned.strftime("%Y-%m-%d"), end_aligned.strftime("%Y-%m-%d"))
    benchmark_return = calculate_benchmark_return(benchmark_df, start_aligned, end_aligned)

    window_tag = f"{start_aligned.strftime('%Y%m%d')}_{end_aligned.strftime('%Y%m%d')}"
    slug = f"phase6f_{args.test}_{window_tag}"
    results_dir = Path("results")

    json_path = results_dir / f"{slug}.json"
    md_path = results_dir / f"{slug}.md"
    baseline_csv = results_dir / f"{slug}_baseline_holdings.csv"
    variant_csv = results_dir / f"{slug}_variant_holdings.csv"

    summary = {
        "window": {
            "start": start_aligned.strftime("%Y-%m-%d"),
            "end": end_aligned.strftime("%Y-%m-%d"),
        },
        "inputs": {
            "test": args.test,
            "momentum_threshold_pct": args.momentum_threshold,
            "stability_threshold": volatility_threshold,
            "commission": args.commission,
            "target_count": args.target_count,
            "pool": args.pool,
        },
        "baseline": baseline_result.as_dict(),
        "variant": variant_result.as_dict(),
        "benchmark": {
            "label": "HS300",
            "total_return": benchmark_return,
        },
        "delta": {
            "total_return": variant_result.total_return - baseline_result.total_return,
            "annual_return": variant_result.annual_return - baseline_result.annual_return,
            "max_drawdown": variant_result.max_drawdown - baseline_result.max_drawdown,
            "avg_turnover": variant_result.avg_turnover - baseline_result.avg_turnover,
        },
    }

    save_json_with_metadata(summary, json_path, phase="Phase 6F", version="1.0.0")
    generate_markdown((start_aligned, end_aligned), baseline_result, variant_result, benchmark_return, md_path)
    save_holdings_csv(baseline_result, baseline_csv)
    save_holdings_csv(variant_result, variant_csv)

    validate_phase6f(baseline_result, variant_result, benchmark_return)


if __name__ == "__main__":
    main()
