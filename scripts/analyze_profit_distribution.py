#!/usr/bin/env python3
"""
Phase 6F: 收益分布分析

目标：
    分析Phase 6E（20股池）2022-2024年单股持仓收益分布
    计算分位数，推荐固定止盈梯度

用法：
    python scripts/analyze_profit_distribution.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 导入phase6d_backtest模块
sys.path.append(str(Path(__file__).parent.parent))
from utils.io import ensure_directories

# 复用phase6d_backtest的数据加载函数
sys.path.append(str(Path(__file__).parent))
from phase6d_backtest import (
    load_stock_pool_from_yaml,
    load_benchmark_data,
    get_year_config,
    load_stock_data,
    backtest_dynamic
)


def strip_emoji(text):
    """
    移除emoji，保留ASCII和中文

    Args:
        text: 原始文本

    Returns:
        str: 去除emoji后的文本
    """
    if not text:
        return ''
    # 保留ASCII字符和中文字符
    return ''.join(c for c in text
                   if ord(c) < 127 or '\u4e00' <= c <= '\u9fff').strip()


def analyze_holding_period_returns(holdings_history, stock_data, rebalance_dates):
    """
    分析每只股票每个持仓周期的收益率

    Args:
        holdings_history: 持仓历史记录
        stock_data: 股票数据字典
        rebalance_dates: 调仓日期列表

    Returns:
        list: [{symbol, start_date, end_date, return_pct}, ...]
    """
    returns = []

    for i in range(len(holdings_history)):
        if i == len(holdings_history) - 1:
            # 最后一期没有卖出
            continue

        current_holdings = holdings_history[i]['stocks']
        next_date_index = i + 1

        if not current_holdings:
            continue

        start_date = rebalance_dates[i]
        end_date = rebalance_dates[next_date_index]

        for symbol in current_holdings:
            if symbol not in stock_data:
                continue

            df = stock_data[symbol]

            if start_date not in df.index or end_date not in df.index:
                continue

            buy_price = df.loc[start_date, 'close']
            sell_price = df.loc[end_date, 'close']

            if buy_price <= 0:
                continue

            return_pct = (sell_price - buy_price) / buy_price * 100

            returns.append({
                'symbol': symbol,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'return_pct': return_pct
            })

    return returns


def calculate_percentiles(returns_data):
    """
    计算收益率分位数

    Args:
        returns_data: 收益率列表

    Returns:
        dict: 分位数统计
    """
    returns_array = np.array([r['return_pct'] for r in returns_data])

    percentiles = {
        'count': len(returns_array),
        'mean': np.mean(returns_array),
        'std': np.std(returns_array),
        'min': np.min(returns_array),
        'p10': np.percentile(returns_array, 10),
        'p25': np.percentile(returns_array, 25),
        'p50': np.percentile(returns_array, 50),
        'p75': np.percentile(returns_array, 75),
        'p90': np.percentile(returns_array, 90),
        'max': np.max(returns_array)
    }

    return percentiles


def recommend_take_profit_levels(percentiles):
    """
    根据分位数推荐止盈梯度

    添加数据质量门禁：
    - 当p50≤0时，不推荐tier1（超过50%持仓亏损）
    - 当p75<10时，不推荐tier2（触发概率过低）
    - 当两者都不满足时，建议不使用固定止盈策略

    Args:
        percentiles: 分位数统计

    Returns:
        dict: 推荐止盈梯度（包含警告和建议）
    """
    p50 = percentiles['p50']
    p75 = percentiles['p75']
    mean = percentiles['mean']

    warnings = []
    tier1 = None
    tier2 = None
    tier1_rationale = None
    tier2_rationale = None

    # 数据质量检查：p50（中位数）
    if p50 <= 0:
        warnings.append(f"⚠️ 警告：中位数={p50:.2f}%≤0，超过50%持仓周期亏损，不适合设置一档止盈")
    else:
        # 向上取整到5的倍数，但不强制≥10%
        tier1_raw = int(np.ceil(p50 / 5) * 5)
        if tier1_raw >= 5:  # 至少5%才有意义
            tier1 = max(5, tier1_raw)
            tier1_rationale = f'基于50%分位数({p50:.1f}%)，平衡收益与频率'
        else:
            warnings.append(f"⚠️ 警告：中位数={p50:.2f}%过低，一档止盈触发概率极低")

    # 数据质量检查：p75（75%分位）
    if p75 < 10:
        warnings.append(f"⚠️ 警告：75%分位={p75:.2f}%<10%，二档止盈触发概率过低（<25%）")
    else:
        # 向上取整到5的倍数
        tier2_raw = int(np.ceil(p75 / 5) * 5)
        tier2 = tier2_raw
        tier2_rationale = f'基于75%分位数({p75:.1f}%)，捕捉强势股'

        # 确保tier2 > tier1
        if tier1 is not None and tier2 <= tier1:
            tier2 = tier1 + 5

    # 检查收益分布特征（右偏分布）
    if mean > p50 and mean - p50 > 2.0:
        warnings.append(f"⚠️ 警告：均值({mean:.2f}%)远大于中位数({p50:.2f}%)，存在右偏分布")
        warnings.append(f"         少数极端正收益拉高均值，固定止盈可能切断尾部收益")

    # 综合判断
    if tier1 is None and tier2 is None:
        return {
            'recommended': False,
            'tier1': None,
            'tier2': None,
            'warnings': warnings,
            'conclusion': '❌ 收益分布不支持固定止盈策略',
            'rationale': {
                'tier1': '不推荐',
                'tier2': '不推荐'
            },
            'reason': '中位数≤0且p75<10，固定止盈将系统性恶化收益'
        }

    return {
        'recommended': True if (tier1 or tier2) else False,
        'tier1': tier1,
        'tier2': tier2,
        'warnings': warnings,
        'rationale': {
            'tier1': tier1_rationale if tier1 else '不推荐',
            'tier2': tier2_rationale if tier2 else '不推荐'
        }
    }


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Phase 6F: 收益分布分析")
    print("="*60 + "\n")

    ensure_directories()

    # 使用Phase 6E配置（20股池，2022-2024）
    pool_name = 'medium_cap'
    years = ['2022', '2023', '2024']

    print(f"✓ 分析配置: {pool_name}池（20股），2022-2024年")

    # 加载沪深300基准（用于获取数据范围）
    benchmark_df = load_benchmark_data(start_date='2022-01-01')

    # 收集所有持仓周期收益
    all_returns = []

    for year in years:
        print(f"\n处理{year}年数据...")

        config = get_year_config(year, 'monthly')
        if not config:
            print(f"  ⚠️ 跳过{year}年（配置不存在）")
            continue

        start_date = config['start_date']
        end_date = config['end_date']
        rebalance_dates = [pd.Timestamp(d) for d in config['rebalance_dates']]

        # 加载股票数据
        data_dir = Path.home() / '.qlib/qlib_data/cn_data'
        stock_data = load_stock_data(data_dir, start_date, end_date, pool_name)

        # 执行回测获取holdings_history
        result = backtest_dynamic(
            stock_data,
            rebalance_dates,
            momentum_threshold=0.0,
            commission=0.0,  # 无佣金，分析纯收益
            target_count=20
        )

        # 分析持仓周期收益
        year_returns = analyze_holding_period_returns(
            result['holdings_history'],
            stock_data,
            rebalance_dates
        )

        all_returns.extend(year_returns)
        print(f"  ✓ {year}年：{len(year_returns)}个持仓周期")

    if not all_returns:
        print("\n❌ 未获取到持仓数据，无法分析")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"收益分布分析（共{len(all_returns)}个持仓周期）")
    print(f"{'='*60}\n")

    # 计算分位数
    percentiles = calculate_percentiles(all_returns)

    print("分位数统计：")
    print(f"  样本数: {percentiles['count']}")
    print(f"  均值: {percentiles['mean']:.2f}%")
    print(f"  标准差: {percentiles['std']:.2f}%")
    print(f"  最小值: {percentiles['min']:.2f}%")
    print(f"  10%分位: {percentiles['p10']:.2f}%")
    print(f"  25%分位: {percentiles['p25']:.2f}%")
    print(f"  50%分位（中位数）: {percentiles['p50']:.2f}%")
    print(f"  75%分位: {percentiles['p75']:.2f}%")
    print(f"  90%分位: {percentiles['p90']:.2f}%")
    print(f"  最大值: {percentiles['max']:.2f}%")

    # 推荐止盈梯度
    recommendations = recommend_take_profit_levels(percentiles)

    print(f"\n{'='*60}")
    print("推荐止盈梯度")
    print(f"{'='*60}\n")

    # 打印警告信息
    if recommendations.get('warnings'):
        for warning in recommendations['warnings']:
            print(warning)
        print()

    # 打印结论
    if 'conclusion' in recommendations:
        print(recommendations['conclusion'])
        print(f"  原因: {recommendations['reason']}")
    else:
        # 打印推荐值
        if recommendations['tier1']:
            print(f"  一档止盈: {recommendations['tier1']}%")
            print(f"    理由: {recommendations['rationale']['tier1']}")
        else:
            print(f"  一档止盈: 不推荐")
            print(f"    理由: {recommendations['rationale']['tier1']}")

        if recommendations['tier2']:
            print(f"  二档止盈: {recommendations['tier2']}%")
            print(f"    理由: {recommendations['rationale']['tier2']}")
        else:
            print(f"  二档止盈: 不推荐")
            print(f"    理由: {recommendations['rationale']['tier2']}")

    # 保存CSV
    df = pd.DataFrame(all_returns)
    output_path = 'results/phase6d_profit_distribution.csv'
    df.to_csv(output_path, index=False)
    print(f"\n✓ 详细数据已保存: {output_path}")

    # 保存分位数统计（添加recommended/reason/warnings字段）
    # 处理warnings：list → 去emoji后用分号拼接
    warnings_list = recommendations.get('warnings', [])
    warnings_clean = [strip_emoji(w) for w in warnings_list]
    warnings_text = '; '.join(warnings_clean)

    # 处理recommended：用1/0（数值友好）
    recommended_flag = 1 if recommendations.get('recommended', True) else 0

    # 处理reason：去除emoji
    if recommendations.get('recommended', True):
        reason = '推荐使用固定止盈策略'
    else:
        reason = strip_emoji(recommendations.get('reason', '收益分布不支持'))

    # 处理None值：转为空字符串（保留合法的 0 值）
    tier1_raw = recommendations.get('tier1')
    tier1_value = '' if tier1_raw is None else tier1_raw
    tier2_raw = recommendations.get('tier2')
    tier2_value = '' if tier2_raw is None else tier2_raw

    summary_df = pd.DataFrame([{
        'metric': 'percentile',
        'count': percentiles['count'],
        'mean': percentiles['mean'],
        'std': percentiles['std'],
        'min': percentiles['min'],
        'p10': percentiles['p10'],
        'p25': percentiles['p25'],
        'p50_median': percentiles['p50'],
        'p75': percentiles['p75'],
        'p90': percentiles['p90'],
        'max': percentiles['max'],
        'recommended_tier1': tier1_value,
        'recommended_tier2': tier2_value,
        'recommended': recommended_flag,
        'reason': reason,
        'warnings_count': len(warnings_list),
        'warnings': warnings_text
    }])

    # 防御性编程：防止 DataFrame 处理过程中引入 NaN
    summary_df[['recommended_tier1', 'recommended_tier2']] = \
        summary_df[['recommended_tier1', 'recommended_tier2']].fillna('')
    
    summary_path = 'results/phase6d_profit_distribution_summary.csv'
    summary_df.to_csv(summary_path, index=False)
    print(f"✓ 分位数统计已保存: {summary_path}")

    print(f"\n{'='*60}")
    print("分析完成")
    print(f"{'='*60}\n")

    # 根据推荐结果给出建议
    if not recommendations.get('recommended', True):
        print("💡 建议：收益分布不支持固定止盈，推荐使用Phase 6E Baseline配置")
        print("  python scripts/phase6d_backtest.py --full --pool medium_cap")
    else:
        print("下一步：使用推荐的止盈梯度进行回测验证")
        tier1_str = recommendations['tier1'] if recommendations['tier1'] else 'None'
        tier2_str = recommendations['tier2'] if recommendations['tier2'] else 'None'
        if recommendations['tier1'] and recommendations['tier2']:
            print(f"  python scripts/phase6d_backtest.py --year 2023 --take-profit {tier1_str},{tier2_str}")
        else:
            print(f"  注意：部分梯度未推荐，请谨慎使用")
    print()


if __name__ == "__main__":
    main()
