#!/usr/bin/env python3
"""
开盘价偏离度统计分析

目的:
    评估开盘价下单策略的可行性
    统计调仓日开盘价 vs 前日收盘价的偏离度

输出:
    - 全局统计：中位数、平均值、标准差
    - 分布分析：正偏离/负偏离比例
    - 详细数据：每个调仓日的偏离情况
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ruamel.yaml import YAML
    yaml = YAML(typ='safe')
except ImportError:
    import yaml


def load_stock_pool():
    """加载medium_cap股票池"""
    yaml_path = Path(__file__).parent.parent / 'stock_pool.yaml'

    with open(yaml_path, 'r', encoding='utf-8') as f:
        if 'ruamel' in sys.modules:
            config = yaml.load(f)
        else:
            config = yaml.safe_load(f)

    stock_pools = config.get('stock_pools', {})
    small_cap_stocks = {s['symbol']: s['name'] for s in stock_pools.get('small_cap', [])}
    medium_cap_config = stock_pools.get('medium_cap', {})
    additional_stocks = {s['symbol']: s['name'] for s in medium_cap_config.get('additional', [])}
    stocks = {**small_cap_stocks, **additional_stocks}

    print(f"✓ 加载medium_cap股票池（{len(stocks)}只）")
    return stocks


def calculate_open_price_deviation(data_dir, stock_pool, rebalance_dates):
    """
    计算开盘价偏离度

    Args:
        data_dir: 数据目录
        stock_pool: 股票池字典
        rebalance_dates: 调仓日期列表

    Returns:
        DataFrame: 偏离度统计结果
    """
    all_deviations = []

    for symbol, name in stock_pool.items():
        csv_file = Path(data_dir) / f'{symbol}.csv'
        if not csv_file.exists():
            continue

        df = pd.read_csv(csv_file, index_col='date', parse_dates=True)

        for date in rebalance_dates:
            date = pd.Timestamp(date)

            # 确保date在数据范围内
            if date not in df.index:
                continue

            # 找前一交易日
            date_loc = df.index.get_loc(date)
            if date_loc == 0:
                continue

            prev_date = df.index[date_loc - 1]

            # 计算偏离度
            prev_close = df.loc[prev_date, 'close']
            open_price = df.loc[date, 'open']

            deviation = (open_price - prev_close) / prev_close

            all_deviations.append({
                'symbol': symbol,
                'name': name,
                'date': date.strftime('%Y-%m-%d'),
                'prev_close': prev_close,
                'open_price': open_price,
                'deviation_pct': deviation * 100
            })

    return pd.DataFrame(all_deviations)


def print_statistics(df):
    """打印统计结果"""
    print("\n" + "=" * 60)
    print("开盘价偏离度统计分析（2024年调仓日）")
    print("=" * 60)

    # 全局统计
    print("\n【全局统计】")
    print(f"样本数量: {len(df)}")
    print(f"平均偏离: {df['deviation_pct'].mean():.3f}%")
    print(f"中位数偏离: {df['deviation_pct'].median():.3f}%")
    print(f"标准差: {df['deviation_pct'].std():.3f}%")
    print(f"最小偏离: {df['deviation_pct'].min():.3f}%")
    print(f"最大偏离: {df['deviation_pct'].max():.3f}%")

    # 分布统计
    print("\n【分布统计】")
    positive = (df['deviation_pct'] > 0).sum()
    negative = (df['deviation_pct'] < 0).sum()
    zero = (df['deviation_pct'] == 0).sum()

    print(f"正偏离（高开）: {positive}次 ({positive/len(df)*100:.1f}%)")
    print(f"负偏离（低开）: {negative}次 ({negative/len(df)*100:.1f}%)")
    print(f"无偏离: {zero}次 ({zero/len(df)*100:.1f}%)")

    # 绝对值统计（不考虑方向）
    df['abs_deviation_pct'] = df['deviation_pct'].abs()
    print("\n【绝对偏离（忽略方向）】")
    print(f"平均绝对偏离: {df['abs_deviation_pct'].mean():.3f}%")
    print(f"中位数绝对偏离: {df['abs_deviation_pct'].median():.3f}%")

    # 按调仓日统计
    print("\n【按调仓日统计】")
    date_stats = df.groupby('date')['deviation_pct'].agg(['mean', 'median', 'std', 'count'])
    print(date_stats.to_string())

    # 决策建议
    print("\n" + "=" * 60)
    print("【决策建议】")
    print("=" * 60)

    median_abs = df['abs_deviation_pct'].median()
    mean_abs = df['abs_deviation_pct'].mean()

    print(f"\n1. 中位数绝对偏离: {median_abs:.3f}%")
    print(f"2. 平均绝对偏离: {mean_abs:.3f}%")

    if median_abs < 0.5:
        print(f"\n✅ **强烈推荐开盘价下单**")
        print(f"   理由：中位数偏离{median_abs:.3f}% < 0.5%，远低于当前溢价1.0%")
        print(f"   预期节省：1.0% - {median_abs:.3f}% = {1.0 - median_abs:.3f}% × 9月 = {(1.0 - median_abs) * 9:.2f}%")
    elif median_abs < 1.0:
        print(f"\n✅ **推荐开盘价下单**")
        print(f"   理由：中位数偏离{median_abs:.3f}% < 1.0%，略低于当前溢价")
        print(f"   预期节省：1.0% - {median_abs:.3f}% = {1.0 - median_abs:.3f}% × 9月 = {(1.0 - median_abs) * 9:.2f}%")
    else:
        print(f"\n⚠️ **谨慎使用开盘价下单**")
        print(f"   理由：中位数偏离{median_abs:.3f}% > 1.0%，可能不如限价+溢价")
        print(f"   预期损失：{median_abs:.3f}% - 1.0% = {median_abs - 1.0:.3f}% × 9月 = {(median_abs - 1.0) * 9:.2f}%")

    # 保存详细数据
    output_file = Path(__file__).parent.parent / 'results' / 'open_price_deviation_2024.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ 详细数据已保存: {output_file}")


def main():
    """主函数"""
    # 加载股票池
    stock_pool = load_stock_pool()

    # 2024年调仓日期
    rebalance_dates = [
        '2024-01-31', '2024-02-29', '2024-03-29', '2024-04-30',
        '2024-05-31', '2024-06-28', '2024-07-31', '2024-08-30',
        '2024-09-30'
    ]

    print(f"\n统计范围: {len(rebalance_dates)}个调仓日")

    # 加载数据并计算偏离度
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    print(f"数据目录: {data_dir}")

    df = calculate_open_price_deviation(data_dir, stock_pool, rebalance_dates)

    if df.empty:
        print("❌ 无数据")
        return

    # 打印统计结果
    print_statistics(df)


if __name__ == '__main__':
    main()
