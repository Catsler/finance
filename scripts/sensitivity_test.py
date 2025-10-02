#!/usr/bin/env python3
"""
Phase 6B: 参数灵敏度测试

⚠️ 注意：
- 该脚本使用 small_cap（10只股票池）
- 这是 Phase 6B 的历史测试，验证参数最优性
- 结论：0%阈值 + MA5>MA10 是最优组合

目标:
    找到Phase 6A动态选股策略的最优参数组合

测试:
    第一轮: 涨幅阈值灵敏度（-5%, 0%, +5%, +10%）
    第二轮: MA条件灵敏度（none, MA5>MA10, MA5>MA20, MA10>MA20）

用法:
    python scripts/sensitivity_test.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys


def load_stock_data_extended(data_dir: Path, start_date='2024-01-01', end_date='2024-09-30') -> dict:
    """
    加载现有10只股票数据，计算MA5/MA10/MA20

    Args:
        data_dir: 数据目录
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        dict: {symbol: DataFrame}
    """
    stocks = {
        '000001.SZ': '平安银行',
        '601318.SH': '中国平安',
        '000858.SZ': '五粮液',
        '600519.SH': '贵州茅台',
        '300750.SZ': '宁德时代',
        '600036.SH': '招商银行',
        '002594.SZ': '比亚迪',
        '000002.SZ': '万科A',
        '600276.SH': '恒瑞医药',
        '601166.SH': '兴业银行'
    }

    data = {}
    for symbol, name in stocks.items():
        csv_file = data_dir / f'{symbol}.csv'
        if not csv_file.exists():
            print(f"❌ 文件不存在: {csv_file}")
            continue

        df = pd.read_csv(csv_file, index_col='date', parse_dates=True)
        df = df[start_date:end_date]
        df['symbol'] = symbol
        df['name'] = name

        # 计算MA5/MA10/MA20
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()

        data[symbol] = df

    print(f"✅ 成功加载 {len(data)} 只股票数据（{start_date} ~ {end_date}）")
    return data


def calculate_20d_return(df: pd.DataFrame, date: str) -> float:
    """计算截至date的过去20个交易日涨幅"""
    try:
        if date not in df.index:
            return np.nan

        date_loc = df.index.get_loc(date)

        if date_loc < 20:
            return np.nan

        current_price = df.loc[date, 'close']
        price_20d_ago = df.iloc[date_loc - 20]['close']

        return (current_price - price_20d_ago) / price_20d_ago

    except Exception as e:
        return np.nan


def check_ma_condition(df: pd.DataFrame, date: str, ma_condition: str) -> bool:
    """
    检查MA条件是否满足

    Args:
        df: 股票数据
        date: 目标日期
        ma_condition: 'none', 'MA5>MA10', 'MA5>MA20', 'MA10>MA20'

    Returns:
        True if 满足条件, else False
    """
    try:
        if date not in df.index:
            return False

        if ma_condition == 'none':
            return True

        if ma_condition == 'MA5>MA10':
            ma5 = df.loc[date, 'ma5']
            ma10 = df.loc[date, 'ma10']
            if pd.isna(ma5) or pd.isna(ma10):
                return False
            return ma5 > ma10

        elif ma_condition == 'MA5>MA20':
            ma5 = df.loc[date, 'ma5']
            ma20 = df.loc[date, 'ma20']
            if pd.isna(ma5) or pd.isna(ma20):
                return False
            return ma5 > ma20

        elif ma_condition == 'MA10>MA20':
            ma10 = df.loc[date, 'ma10']
            ma20 = df.loc[date, 'ma20']
            if pd.isna(ma10) or pd.isna(ma20):
                return False
            return ma10 > ma20

        else:
            raise ValueError(f"未知的MA条件: {ma_condition}")

    except Exception as e:
        return False


def select_stocks_parameterized(
    stock_data: dict,
    date: str,
    momentum_threshold: float = 0.0,
    ma_condition: str = 'MA5>MA10'
) -> list:
    """
    参数化选股

    Args:
        stock_data: 所有股票数据
        date: 选股日期
        momentum_threshold: 20日涨幅阈值（如0.0表示>0%，0.05表示>5%）
        ma_condition: MA条件

    Returns:
        list: 选中的股票代码
    """
    selected = []

    for symbol, df in stock_data.items():
        # 条件1: 20日涨幅 > threshold
        ret_20d = calculate_20d_return(df, date)
        if pd.isna(ret_20d) or ret_20d <= momentum_threshold:
            continue

        # 条件2: MA条件
        ma_check = check_ma_condition(df, date, ma_condition)
        if not ma_check:
            continue

        selected.append(symbol)

    return selected


def backtest_dynamic_parameterized(
    stock_data: dict,
    momentum_threshold: float,
    ma_condition: str,
    initial_capital: float = 100000,
    verbose: bool = False
) -> dict:
    """
    参数化动态选股回测

    Args:
        stock_data: 股票数据
        momentum_threshold: 动量阈值
        ma_condition: MA条件
        initial_capital: 初始资金
        verbose: 是否打印调仓详情

    Returns:
        dict: 回测结果
    """
    # 月末调仓日期
    rebalance_dates = [
        '2024-01-31', '2024-02-29', '2024-03-29',
        '2024-04-30', '2024-05-31', '2024-06-28',
        '2024-07-31', '2024-08-30', '2024-09-30'
    ]

    rebalance_dates = [pd.Timestamp(d) for d in rebalance_dates]

    holdings_history = []
    current_value = initial_capital
    total_turnover = 0

    for i, date in enumerate(rebalance_dates):
        # 选股
        selected = select_stocks_parameterized(
            stock_data,
            date,
            momentum_threshold,
            ma_condition
        )

        if not selected:
            if verbose:
                print(f"  ⚠️  {date.strftime('%Y-%m-%d')}: 无股票通过筛选")
            holdings_history.append({
                'date': date,
                'stocks': [],
                'count': 0
            })
            continue

        holdings_history.append({
            'date': date,
            'stocks': selected.copy(),
            'count': len(selected)
        })

        # 计算换手
        if i > 0:
            prev_holdings = set(holdings_history[i-1]['stocks'])
            curr_holdings = set(selected)
            turnover = len(prev_holdings.symmetric_difference(curr_holdings))
            total_turnover += turnover

        # 计算收益到下一个调仓日
        if i < len(rebalance_dates) - 1:
            next_date = rebalance_dates[i + 1]
            capital_per_stock = current_value / len(selected)
            period_value = 0

            for symbol in selected:
                df = stock_data[symbol]

                if date not in df.index or next_date not in df.index:
                    period_value += capital_per_stock
                    continue

                buy_price = df.loc[date, 'close']
                sell_price = df.loc[next_date, 'close']

                shares = capital_per_stock / buy_price
                period_value += shares * sell_price

            current_value = period_value

    total_return = (current_value - initial_capital) / initial_capital
    turnover_rate = total_turnover / (len(rebalance_dates) * 10) * 100

    # 计算持仓均值和空仓月数
    avg_holdings = np.mean([r['count'] for r in holdings_history])
    empty_months = sum(1 for r in holdings_history if r['count'] == 0)

    return {
        'final_value': current_value,
        'total_return': total_return,
        'turnover': turnover_rate,
        'avg_holdings': avg_holdings,
        'empty_months': empty_months,
        'holdings_history': holdings_history
    }


def print_results_table(results: list, title: str):
    """打印结果表格"""
    print("\n" + "="*80)
    print(f"【{title}】")
    print("="*80 + "\n")

    # 表头
    print(f"{'组别':<6} {'参数':<12} {'总收益':<10} {'成本':<8} {'净收益':<10} "
          f"{'换手率':<10} {'持仓均值':<10} {'空仓月数':<8}")
    print("-"*80)

    # 数据行
    for r in results:
        print(f"{r['组别']:<6} {r['参数']:<12} {r['总收益']:<10} {r['成本']:<8} "
              f"{r['净收益']:<10} {r['换手率']:<10} {r['持仓均值']:<10} {r['空仓月数']:<8}")

    print("="*80)


def run_phase_1(stock_data: dict) -> list:
    """
    第一轮: 涨幅阈值灵敏度测试

    Args:
        stock_data: 股票数据

    Returns:
        list: 推荐进入第二轮的阈值
    """
    print("\n" + "="*80)
    print("Phase 6B-1: 涨幅阈值灵敏度测试（固定MA5>MA10）")
    print("="*80)

    thresholds = [-0.05, 0.0, 0.05, 0.10]  # -5%, 0%, +5%, +10%
    threshold_labels = ['-5%', '0%', '+5%', '+10%']
    results = []

    # 保守成本：每次调仓0.33%
    COST_PER_REBALANCE = 0.0033
    NUM_REBALANCES = 8  # 9个月，第1次不算换手，最后1次算卖出

    for i, (threshold, label) in enumerate(zip(thresholds, threshold_labels)):
        print(f"\n正在测试组A{i+1}（阈值 {label}）...")

        result = backtest_dynamic_parameterized(
            stock_data,
            momentum_threshold=threshold,
            ma_condition='MA5>MA10',
            verbose=False
        )

        # 保守估算成本
        estimated_cost = NUM_REBALANCES * COST_PER_REBALANCE
        net_return = result['total_return'] - estimated_cost

        results.append({
            '组别': f'A{i+1}',
            '参数': label,
            '总收益': f"{result['total_return']*100:.2f}%",
            '成本': f"{estimated_cost*100:.2f}%",
            '净收益': f"{net_return*100:.2f}%",
            '换手率': f"{result['turnover']:.2f}%",
            '持仓均值': f"{result['avg_holdings']:.1f}只",
            '空仓月数': str(result['empty_months']),
            '_net_return': net_return,  # 用于排序
            '_turnover': result['turnover'],  # 用于排序
            '_threshold': threshold  # 用于第二轮
        })

    # 打印表格
    print_results_table(results, "第一轮测试结果")

    # 自动筛选
    print("\n" + "="*80)
    print("【自动筛选建议】")
    print("="*80 + "\n")

    # 候选1: 净收益最高
    candidate1 = max(results, key=lambda x: x['_net_return'])
    print(f"候选1: {candidate1['参数']} (净收益最高 {candidate1['净收益']})")

    # 候选2: 净收益前2中换手率最低
    top2_return = sorted(results, key=lambda x: x['_net_return'], reverse=True)[:2]
    candidate2 = min(top2_return, key=lambda x: x['_turnover'])
    print(f"候选2: {candidate2['参数']} (收益前2中换手最低 {candidate2['换手率']})")

    # 返回推荐阈值
    recommended = []
    recommended.append(candidate1['_threshold'])
    if candidate2['_threshold'] != candidate1['_threshold']:
        recommended.append(candidate2['_threshold'])

    print(f"\n推荐进入第二轮的阈值: {[f'{t*100:.0f}%' if t != 0 else '0%' for t in recommended]}")
    print("\n请确认后手动调用 run_phase_2() 进行第二轮测试")

    return recommended


def run_phase_2(stock_data: dict, thresholds: list):
    """
    第二轮: MA条件灵敏度测试

    Args:
        stock_data: 股票数据
        thresholds: 第一轮选出的阈值列表
    """
    print("\n" + "="*80)
    print("Phase 6B-2: MA条件灵敏度测试")
    print("="*80)

    ma_conditions = ['none', 'MA5>MA10', 'MA5>MA20', 'MA10>MA20']
    COST_PER_REBALANCE = 0.0033
    NUM_REBALANCES = 8

    all_results = []

    for threshold in thresholds:
        threshold_label = f"{threshold*100:+.0f}%" if threshold != 0 else "0%"
        print(f"\n--- 测试阈值 {threshold_label} ---")

        results = []

        for i, ma_cond in enumerate(ma_conditions):
            print(f"  正在测试 MA条件: {ma_cond}...")

            result = backtest_dynamic_parameterized(
                stock_data,
                momentum_threshold=threshold,
                ma_condition=ma_cond,
                verbose=False
            )

            estimated_cost = NUM_REBALANCES * COST_PER_REBALANCE
            net_return = result['total_return'] - estimated_cost

            group_id = f"B{len(all_results)+1}"
            results.append({
                '组别': group_id,
                '参数': f"{threshold_label},{ma_cond}",
                '总收益': f"{result['total_return']*100:.2f}%",
                '成本': f"{estimated_cost*100:.2f}%",
                '净收益': f"{net_return*100:.2f}%",
                '换手率': f"{result['turnover']:.2f}%",
                '持仓均值': f"{result['avg_holdings']:.1f}只",
                '空仓月数': str(result['empty_months']),
                '_net_return': net_return,
                '_turnover': result['turnover']
            })
            all_results.append(results[-1])

        # 打印当前阈值的结果
        print_results_table(results, f"阈值 {threshold_label} 的MA条件测试")

    # 打印最优建议
    print("\n" + "="*80)
    print("【最优参数建议】")
    print("="*80 + "\n")

    best = max(all_results, key=lambda x: x['_net_return'])
    print(f"最优组合: {best['组别']} - {best['参数']}")
    print(f"  净收益: {best['净收益']}")
    print(f"  换手率: {best['换手率']}")
    print(f"  持仓均值: {best['持仓均值']}")
    print(f"  空仓月数: {best['空仓月数']}")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("Phase 6B: 参数灵敏度测试")
    print("="*80 + "\n")

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data_extended(data_dir)

    if not stock_data:
        print("❌ 无法加载数据，请检查数据目录")
        sys.exit(1)

    print()

    # 第一轮测试
    recommended_thresholds = run_phase_1(stock_data)

    # 第二轮测试
    print("\n" + "="*80)
    print("开始第二轮测试...")
    print("="*80)
    run_phase_2(stock_data, recommended_thresholds)


if __name__ == "__main__":
    main()
