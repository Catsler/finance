#!/usr/bin/env python3
"""
Phase 8: 市场分化度计算工具

计算指定年份股票池的收益率变异系数（CV）
CV = std(returns) / abs(mean(returns))

用途：
- CV < 0.5: 低分化（单边市）
- CV 0.5-1.0: 中等分化
- CV > 1.0: 高分化（轮动市）
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.phase6d_backtest import load_stock_pool_from_yaml, load_stock_data


def calculate_dispersion(stock_data, year):
    """
    计算指定年份的市场分化度

    Args:
        stock_data: 股票数据字典 {symbol: DataFrame}
        year: 年份（如2019）

    Returns:
        dict: {
            'cv': 变异系数,
            'mean_return': 平均收益率,
            'std_return': 收益率标准差,
            'individual_returns': 个股收益率列表
        }
    """
    year_start = pd.Timestamp(f'{year}-01-01')
    year_end = pd.Timestamp(f'{year}-12-31')

    annual_returns = []

    for symbol, df in stock_data.items():
        # 筛选年度数据（date是index）
        year_data = df[(df.index >= year_start) & (df.index <= year_end)]

        if len(year_data) < 10:  # 数据点太少，跳过
            print(f"  ⚠️ {symbol}: 数据不足（{len(year_data)}个交易日）")
            continue

        # 计算年度收益率
        start_price = year_data.iloc[0]['close']
        end_price = year_data.iloc[-1]['close']
        annual_return = (end_price / start_price - 1) * 100

        annual_returns.append({
            'symbol': symbol,
            'return': annual_return
        })

    if len(annual_returns) < 5:  # 样本太少
        return None

    # 提取收益率
    returns = np.array([r['return'] for r in annual_returns])
    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)

    # 计算 CV（处理均值接近0的情况）
    if abs(mean_return) < 0.01:
        cv = np.inf  # 均值接近0时CV无意义
    else:
        cv = std_return / abs(mean_return)

    return {
        'cv': cv,
        'mean_return': mean_return,
        'std_return': std_return,
        'individual_returns': annual_returns,
        'sample_size': len(annual_returns)
    }


def main():
    parser = argparse.ArgumentParser(description='计算市场分化度（CV）')
    parser.add_argument('--year', type=int, required=True, help='年份（如2019）')
    parser.add_argument('--pool', default='legacy_7stocks',
                       help='股票池名称（默认legacy_7stocks）')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Phase 8: 市场分化度计算 - {args.year}年")
    print(f"{'='*60}\n")

    # 1. 加载股票池
    stocks = load_stock_pool_from_yaml(args.pool)

    # 2. 加载股票数据
    start_date = f'{args.year}-01-01'
    end_date = f'{args.year}-12-31'

    print(f"✓ 加载 {len(stocks)} 只股票（{start_date} ~ {end_date}）\n")
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data(data_dir, start_date, end_date, pool_name=args.pool)

    # 3. 计算分化度
    result = calculate_dispersion(stock_data, args.year)

    if result is None:
        print("❌ 样本不足，无法计算分化度")
        return

    # 4. 输出结果
    print(f"\n{'─'*60}")
    print(f"分化度分析结果")
    print(f"{'─'*60}")
    print(f"样本数量: {result['sample_size']}只股票")
    print(f"平均收益: {result['mean_return']:.2f}%")
    print(f"收益标准差: {result['std_return']:.2f}%")
    print(f"变异系数(CV): {result['cv']:.2f}")

    # 分化度判定
    if result['cv'] < 0.5:
        level = "低分化（单边市）"
    elif result['cv'] < 1.0:
        level = "中等分化"
    else:
        level = "高分化（轮动市）"

    print(f"分化等级: {level}")

    # 5. 个股明细
    print(f"\n{'─'*60}")
    print(f"个股年度收益率")
    print(f"{'─'*60}")

    sorted_returns = sorted(result['individual_returns'],
                          key=lambda x: x['return'], reverse=True)

    for item in sorted_returns:
        symbol = item['symbol']
        ret = item['return']
        name = stocks.get(symbol, symbol)
        print(f"{symbol:12s} ({name:8s}): {ret:+7.2f}%")

    print()


if __name__ == '__main__':
    main()
