#!/usr/bin/env python3
"""
HS300 智能选股系统 - MVP版本 (v1.1)

功能流程:
    1. 获取沪深300成分股列表（带缓存）
    2. 批量下载成分股数据（带断点续传+重试）
    3. 筛选符合条件的股票（20日涨幅>0%, MA5>MA10）
    4. 等权分配仓位（预算10万元，取整手数）
    5. 输出持仓建议到JSON文件

用法:
    python scripts/hs300_selector.py                    # 使用默认预算10万元
    python scripts/hs300_selector.py --budget 100000 --top 5
    python scripts/hs300_selector.py --budget 50000 --top 3 --skip-download

参数:
    --budget: 总预算（元，默认100000）
    --top: 选取前N只股票（默认5，建议3-5）
    --force-refresh: 强制刷新HS300成分股（忽略缓存）
    --skip-download: 跳过数据下载（假设数据已存在）
    --momentum-threshold: 20日涨幅阈值（百分比，默认0.0）

改进 (v1.1):
    - 默认预算调整为10万元（符合实际场景）
    - 增加预算合理性校验（低于2万元会报错）
    - 分配结果包含 unaffordable 信息（因预算不足被排除的股票）
    - 控制台输出操作建议（增加预算或降低选股数）
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# 导入工具
sys.path.append(str(Path(__file__).parent.parent))
from utils.io import save_json_with_metadata


# ===== 配置区 =====
QLIB_DATA_DIR = Path.home() / ".qlib/qlib_data/cn_data"
HS300_CACHE_FILE = Path("results/hs300_constituents.json")
HS300_CACHE_DAYS = 7  # 缓存有效期（天）
MAX_RETRIES = 3  # 下载重试次数
DOWNLOAD_TIMEOUT = 120  # 单只股票下载超时（秒）

# 预算配置
DEFAULT_BUDGET = 100000  # 默认10万元（符合实际场景）
MIN_REQUIRED_BUDGET = 20000  # 最低门槛（估算1手最低成本）


# ===== 预算合理性校验 =====
def validate_budget(budget, top_n):
    """
    预算合理性校验（快速失败原则）

    Args:
        budget: 用户预算（元）
        top_n: 目标持仓数

    Raises:
        ValueError: 预算明显不足
    """
    if budget < MIN_REQUIRED_BUDGET:
        raise ValueError(
            f"预算 {budget:.0f} 元可能不足以构建持仓\n"
            f"   建议最低预算: {MIN_REQUIRED_BUDGET} 元\n"
            f"   （基于当前市场价格水平，买{top_n}只股票各1手）"
        )

    # 警告阈值（预算偏低但可能勉强够用）
    recommended_budget = top_n * 30000  # 每只3万元（经验值）
    if budget < recommended_budget:
        print(f"⚠️ 预算 {budget:.0f} 元偏低")
        print(f"   推荐预算: {recommended_budget:.0f} 元以上（买{top_n}只）")
        print(f"   当前配置可能导致部分高价股买不起\n")


# ===== Phase 1: 获取 HS300 成分股 =====
def fetch_hs300_constituents(force_refresh=False):
    """
    获取沪深300成分股列表（带7天缓存）

    Args:
        force_refresh: 是否强制刷新（忽略缓存）

    Returns:
        dict: {symbol: name}
    """
    # 检查缓存
    if not force_refresh and HS300_CACHE_FILE.exists():
        with open(HS300_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        cache_time = datetime.fromisoformat(cache['timestamp'])
        age_days = (datetime.now() - cache_time).days

        if age_days < HS300_CACHE_DAYS:
            print(f"✓ 从缓存加载 HS300 成分股（{age_days}天前更新）")
            return cache['constituents']
        else:
            print(f"⚠️ 缓存已过期（{age_days}天），重新获取...")

    # 获取最新成分股
    print("正在获取沪深300成分股列表...")
    try:
        import akshare as ak
        df = ak.index_stock_cons(symbol='000300')

        # 转换为标准格式（添加 .SH/.SZ 后缀）
        constituents = {}
        for _, row in df.iterrows():
            code = row['品种代码']
            name = row['品种名称']

            # 自动判断市场后缀
            if code.startswith('6'):
                symbol = f"{code}.SH"
            else:
                symbol = f"{code}.SZ"

            constituents[symbol] = name

        print(f"✓ 获取 {len(constituents)} 只 HS300 成分股")

        # 保存缓存
        HS300_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'constituents': constituents,
            'count': len(constituents)
        }

        with open(HS300_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 缓存已保存: {HS300_CACHE_FILE}")
        return constituents

    except Exception as e:
        print(f"❌ 获取 HS300 成分股失败: {e}")
        sys.exit(1)


# ===== Phase 2: 批量下载数据（带断点续传） =====
def download_stock_with_retry(symbol, years=1, max_retries=MAX_RETRIES):
    """
    下载单只股票数据（带重试机制）

    Args:
        symbol: 股票代码
        years: 回溯年数
        max_retries: 最大重试次数

    Returns:
        bool: 是否成功
    """
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [
                    "python3",
                    "scripts/akshare-to-qlib-converter.py",
                    "--symbol", symbol,
                    "--years", str(years),
                ],
                capture_output=True,
                text=True,
                timeout=DOWNLOAD_TIMEOUT,
            )

            if result.returncode == 0:
                return True
            else:
                print(f"  ⚠️ 尝试 {attempt + 1}/{max_retries} 失败")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避

        except subprocess.TimeoutExpired:
            print(f"  ⚠️ 超时（>{DOWNLOAD_TIMEOUT}s），尝试 {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except Exception as e:
            print(f"  ⚠️ 异常: {e}")
            break

    return False


def batch_download_hs300(constituents, skip_existing=True):
    """
    批量下载 HS300 成分股数据（带断点续传）

    Args:
        constituents: 成分股字典 {symbol: name}
        skip_existing: 是否跳过已存在的文件

    Returns:
        dict: 下载统计 {success: int, failed: list, skipped: int}
    """
    print(f"\n{'='*60}")
    print(f"开始下载 {len(constituents)} 只 HS300 成分股数据")
    print(f"{'='*60}")

    stats = {
        'success': 0,
        'failed': [],
        'skipped': 0,
        'total': len(constituents)
    }

    for i, (symbol, name) in enumerate(constituents.items(), 1):
        print(f"\n[{i}/{len(constituents)}] {symbol} {name}")

        # 断点续传：检查文件是否已存在
        csv_file = QLIB_DATA_DIR / f"{symbol}.csv"
        if skip_existing and csv_file.exists():
            print(f"  ✓ 文件已存在，跳过下载")
            stats['skipped'] += 1
            continue

        # 下载（带重试）
        success = download_stock_with_retry(symbol, years=1)

        if success:
            print(f"  ✅ 下载成功")
            stats['success'] += 1
        else:
            print(f"  ❌ 下载失败（已重试{MAX_RETRIES}次）")
            stats['failed'].append(symbol)

    # 打印统计
    print(f"\n{'='*60}")
    print(f"下载完成统计:")
    print(f"  成功: {stats['success']}")
    print(f"  跳过: {stats['skipped']}")
    print(f"  失败: {len(stats['failed'])}")
    print(f"  总计: {stats['total']}")

    if stats['failed']:
        print(f"\n失败列表: {', '.join(stats['failed'])}")

    print(f"{'='*60}\n")

    return stats


# ===== Phase 3: 动量策略筛选 =====
def load_stock_data(symbol, name):
    """
    加载单只股票数据并计算指标

    Returns:
        dict or None: {symbol, name, date, close, ma5, ma10, return_20d}
    """
    csv_path = QLIB_DATA_DIR / f"{symbol}.csv"
    if not csv_path.exists():
        return None

    try:
        df = pd.read_csv(csv_path, parse_dates=["date"], index_col="date")
        df = df.sort_index()

        if df.empty or len(df) < 30:  # 至少需要30天数据
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
            return None

        latest_date = df.index[latest_idx]
        loc = df.index.get_loc(latest_date)

        # 计算20日涨幅
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

    except Exception as e:
        print(f"⚠️ 加载 {symbol} 失败: {e}")
        return None


def filter_by_momentum(constituents, momentum_threshold=0.0):
    """
    筛选符合动量条件的股票

    条件:
        1. 20日涨幅 > threshold (默认0%)
        2. MA5 > MA10

    Args:
        constituents: 成分股字典
        momentum_threshold: 涨幅阈值（百分比）

    Returns:
        list: 符合条件的股票列表（按涨幅降序）
    """
    print(f"\n{'='*60}")
    print(f"筛选条件: 20日涨幅>{momentum_threshold}%, MA5>MA10")
    print(f"{'='*60}")

    selected = []
    rejected_count = 0

    for symbol, name in constituents.items():
        data = load_stock_data(symbol, name)

        if data is None:
            rejected_count += 1
            continue

        # 检查条件
        if data["return_20d"] is None or data["return_20d"] <= momentum_threshold / 100:
            rejected_count += 1
            continue

        if data["ma5"] <= data["ma10"]:
            rejected_count += 1
            continue

        # 符合条件
        selected.append(data)

    # 按涨幅降序排序
    selected.sort(key=lambda x: x["return_20d"], reverse=True)

    print(f"筛选结果: {len(selected)}/{len(constituents)} 只股票符合条件")
    print(f"剔除: {rejected_count} 只（无数据或不符合条件）")

    return selected


# ===== Phase 4: 等权仓位分配 =====
def allocate_equal_weight(selected_stocks, budget, top_n=5):
    """
    等权分配仓位（取整手数，1手=100股）- 增强版

    Args:
        selected_stocks: 筛选出的股票列表
        budget: 总预算（元）
        top_n: 选取前N只股票

    Returns:
        dict: {
            'positions': [...],      # 成功分配的持仓
            'unaffordable': [...],   # 因预算不足被排除的股票
            'total_cost': float,
            'utilization': float,
            'warning': str or None   # 友好提示信息
        }
    """
    if not selected_stocks:
        return {
            'positions': [],
            'unaffordable': [],
            'total_cost': 0,
            'budget': budget,
            'utilization': 0,
            'count': 0,
            'message': '无符合条件的股票，建议空仓'
        }

    # 取前N只
    top_stocks = selected_stocks[:min(top_n, len(selected_stocks))]
    allocation_per_stock = budget / len(top_stocks)

    positions = []
    unaffordable = []
    total_cost = 0

    for stock in top_stocks:
        price = stock['close']
        min_cost = price * 100  # 1手最低成本

        # 判断可负担性
        if min_cost > allocation_per_stock:
            unaffordable.append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'price': price,
                'min_cost': round(min_cost, 2),
                'allocated_budget': round(allocation_per_stock, 2),
                'shortage': round(min_cost - allocation_per_stock, 2),
                'return_20d': round(stock['return_20d'] * 100, 2),
                'reason': f"1手需{min_cost:.0f}元 > 分配{allocation_per_stock:.0f}元"
            })
            continue

        # 可负担：计算手数（向下取整）
        lots = int(allocation_per_stock / price / 100)

        if lots == 0:
            # 理论上不应该到这里（已被上面的 min_cost 检查捕获）
            unaffordable.append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'price': price,
                'min_cost': round(min_cost, 2),
                'allocated_budget': round(allocation_per_stock, 2),
                'shortage': round(min_cost - allocation_per_stock, 2),
                'return_20d': round(stock['return_20d'] * 100, 2),
                'reason': f"计算手数为0"
            })
            continue

        shares = lots * 100
        cost = shares * price

        positions.append({
            'symbol': stock['symbol'],
            'name': stock['name'],
            'price': price,
            'lots': lots,
            'shares': shares,
            'cost': round(cost, 2),
            'weight': round(cost / budget * 100, 2),
            'return_20d': round(stock['return_20d'] * 100, 2),
            'ma5': stock['ma5'],
            'ma10': stock['ma10']
        })

        total_cost += cost

    # 生成警告信息
    warning = None
    if unaffordable:
        warning = (
            f"{len(unaffordable)}只候选股票因预算不足被排除 "
            f"(总预算{budget:.0f}元 ÷ {len(top_stocks)}只 = {allocation_per_stock:.0f}元/只)"
        )

    return {
        'positions': positions,
        'unaffordable': unaffordable,
        'total_cost': round(total_cost, 2),
        'budget': budget,
        'utilization': round(total_cost / budget * 100, 2) if budget > 0 else 0,
        'count': len(positions),
        'warning': warning
    }


# ===== Main 流程 =====
def main():
    parser = argparse.ArgumentParser(description="HS300 智能选股系统")
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET,
                       help=f"总预算（元，默认{DEFAULT_BUDGET}）")
    parser.add_argument("--top", type=int, default=5, help="选取前N只股票（建议3-5）")
    parser.add_argument("--force-refresh", action="store_true", help="强制刷新 HS300 成分股")
    parser.add_argument("--skip-download", action="store_true", help="跳过数据下载")
    parser.add_argument("--momentum-threshold", type=float, default=0.0, help="20日涨幅阈值（百分比）")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("HS300 智能选股系统 - MVP版本")
    print("="*60)
    print(f"预算: {args.budget}元 | 候选数: {args.top}只 | 动量阈值: {args.momentum_threshold}%")
    print("="*60)

    # 预算合理性校验
    try:
        validate_budget(args.budget, args.top)
    except ValueError as e:
        print(f"\n❌ 参数错误:\n{e}\n")
        sys.exit(1)

    # Phase 1: 获取 HS300 成分股
    constituents = fetch_hs300_constituents(force_refresh=args.force_refresh)

    # Phase 2: 批量下载数据
    if not args.skip_download:
        download_stats = batch_download_hs300(constituents, skip_existing=True)

        if download_stats['success'] + download_stats['skipped'] < 100:
            print(f"⚠️ 仅成功下载 {download_stats['success']} 只，可能影响筛选结果")

    # Phase 3: 筛选股票
    selected = filter_by_momentum(constituents, momentum_threshold=args.momentum_threshold)

    if selected:
        print(f"\n{'='*60}")
        print(f"Top {min(args.top, len(selected))} 候选股票（按20日涨幅排序）:")
        print(f"{'='*60}")
        for i, stock in enumerate(selected[:args.top], 1):
            print(f"{i}. {stock['symbol']}\t{stock['name']:8s}\t涨幅:{stock['return_20d']*100:>6.2f}%\t价格:{stock['close']:.2f}")

    # Phase 4: 仓位分配
    allocation = allocate_equal_weight(selected, args.budget, args.top)

    # 输出结果
    print(f"\n{'='*60}")
    print("📊 持仓建议（等权分配）:")
    print(f"{'='*60}")

    if allocation['positions']:
        for pos in allocation['positions']:
            print(f"  {pos['symbol']}\t{pos['name']:8s}\t{pos['lots']}手\t成本:{pos['cost']:.2f}元\t占比:{pos['weight']:.1f}%")

        print(f"{'-'*60}")
        print(f"  总成本: {allocation['total_cost']:.2f}元")
        print(f"  预算利用率: {allocation['utilization']:.1f}%")
        print(f"  剩余: {args.budget - allocation['total_cost']:.2f}元")
    else:
        print(f"  {allocation.get('message', '无可用持仓')}")

    # 输出不可负担的股票
    if allocation.get('unaffordable'):
        print(f"\n{'='*60}")
        print("⚠️ 因预算不足被排除的股票:")
        print(f"{'='*60}")
        for stock in allocation['unaffordable']:
            print(f"  {stock['symbol']}\t{stock['name']:8s}\t"
                  f"涨幅:{stock['return_20d']:>6.2f}%\t"
                  f"价格:{stock['price']:.2f}\t"
                  f"缺口:{stock['shortage']:.0f}元")

        print(f"\n💡 建议:")
        if allocation['positions']:
            # 有部分持仓
            total_shortage = sum(s['shortage'] for s in allocation['unaffordable'])
            print(f"   1. 增加预算 {total_shortage:.0f} 元可买入全部{len(allocation['unaffordable'])}只")
        else:
            # 完全空仓
            min_shortage = min(s['min_cost'] for s in allocation['unaffordable'])
            print(f"   1. 至少增加到 {min_shortage:.0f} 元可买入1只")
            affordable_count = int(args.budget / min_shortage) if min_shortage > 0 else 0
            if affordable_count > 0:
                print(f"   2. 或降低选股数 --top {affordable_count}")

    print(f"{'='*60}")

    # 保存结果
    date_str = datetime.now().strftime('%Y%m%d')
    output_file = Path(f"results/hs300_selection_{date_str}.json")

    result = {
        'selection_date': datetime.now().strftime('%Y-%m-%d'),
        'strategy': 'HS300动量策略',
        'parameters': {
            'budget': args.budget,
            'top_n': args.top,
            'momentum_threshold': args.momentum_threshold
        },
        'constituents_count': len(constituents),
        'selected_count': len(selected),
        'allocation': allocation,
        'top_candidates': [
            {
                'symbol': s['symbol'],
                'name': s['name'],
                'return_20d': round(s['return_20d'] * 100, 2),
                'close': s['close']
            }
            for s in selected[:10]  # 保存前10只候选
        ]
    }

    save_json_with_metadata(
        result,
        output_file,
        phase='Phase 1 MVP',
        version='1.0.0'
    )

    print(f"\n✓ 选股结果已保存: {output_file}")


if __name__ == "__main__":
    main()
