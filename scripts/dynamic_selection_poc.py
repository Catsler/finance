#!/usr/bin/env python3
"""
Phase 6A-PoC: 动态选股验证

⚠️ 注意：
- 该脚本使用 small_cap（10只股票池）
- 这是 Phase 6A 的历史 PoC，用于2024年验证
- 如需20只池回测，请使用：python scripts/phase6d_backtest.py --full

目标:
    验证"动态选股+月度调仓"是否优于"固定持仓+买入持有"

策略:
    场景1（固定持仓）: 10只股票等权配置，买入持有
    场景2（动态选股）: 每月月末筛选，等权配置选中股票

选股规则（单一动量因子）:
    1. 过去20个交易日涨幅 > 0%
    2. MA5 > MA10（当日）

用法:
    python scripts/dynamic_selection_poc.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys


def load_stock_data(data_dir: Path, start_date='2024-01-01', end_date='2024-09-30') -> dict:
    """
    加载现有10只股票数据，过滤2024年

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

        # 计算MA5和MA10
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()

        data[symbol] = df

    print(f"✅ 成功加载 {len(data)} 只股票数据（{start_date} ~ {end_date}）")
    return data


def calculate_20d_return(df: pd.DataFrame, date: str) -> float:
    """
    计算截至date的过去20个交易日涨幅

    Args:
        df: 股票数据
        date: 目标日期

    Returns:
        20日涨幅（小数）
    """
    try:
        if date not in df.index:
            return np.nan

        # 获取date的位置
        date_loc = df.index.get_loc(date)

        # 如果不足20个交易日，返回nan
        if date_loc < 20:
            return np.nan

        # 计算20日涨幅
        current_price = df.loc[date, 'close']
        price_20d_ago = df.iloc[date_loc - 20]['close']

        return (current_price - price_20d_ago) / price_20d_ago

    except Exception as e:
        return np.nan


def check_ma_crossover(df: pd.DataFrame, date: str) -> bool:
    """
    检查date当日MA5是否>MA10

    Args:
        df: 股票数据
        date: 目标日期

    Returns:
        True if MA5 > MA10, else False
    """
    try:
        if date not in df.index:
            return False

        ma5 = df.loc[date, 'ma5']
        ma10 = df.loc[date, 'ma10']

        if pd.isna(ma5) or pd.isna(ma10):
            return False

        return ma5 > ma10

    except Exception as e:
        return False


def select_stocks(stock_data: dict, date: str) -> list:
    """
    月度选股：返回通过筛选的股票列表

    筛选条件（AND逻辑）:
        1. 过去20日涨幅 > 0%
        2. MA5 > MA10

    Args:
        stock_data: 所有股票数据
        date: 选股日期

    Returns:
        list: 选中的股票代码
    """
    selected = []

    for symbol, df in stock_data.items():
        # 条件1: 20日涨幅 > 0
        ret_20d = calculate_20d_return(df, date)
        if pd.isna(ret_20d) or ret_20d <= 0:
            continue

        # 条件2: MA5 > MA10
        ma_cross = check_ma_crossover(df, date)
        if not ma_cross:
            continue

        selected.append(symbol)

    return selected


def backtest_fixed(stock_data: dict, initial_capital: float = 100000) -> dict:
    """
    场景1: 固定持仓回测

    策略:
        - 10只股票等权配置
        - 2024-01-01买入，2024-09-30卖出
        - 中间不调仓

    Args:
        stock_data: 股票数据
        initial_capital: 初始资金

    Returns:
        dict: 回测结果
    """
    # 每只股票分配资金
    capital_per_stock = initial_capital / len(stock_data)

    total_value = 0

    for symbol, df in stock_data.items():
        # 买入价（第一个有效交易日）
        first_date = df.index[0]
        buy_price = df.loc[first_date, 'close']

        # 卖出价（最后一个交易日）
        last_date = df.index[-1]
        sell_price = df.loc[last_date, 'close']

        # 计算持仓收益
        shares = capital_per_stock / buy_price
        final_value = shares * sell_price

        total_value += final_value

    total_return = (total_value - initial_capital) / initial_capital

    return {
        'final_value': total_value,
        'total_return': total_return,
        'turnover': 0  # 买入持有，换手率为0
    }


def backtest_dynamic(stock_data: dict, initial_capital: float = 100000) -> dict:
    """
    场景2: 动态选股回测

    策略:
        - 每月月末筛选通过的股票
        - 等权配置选中股票
        - 下月月末重新筛选+调仓

    Args:
        stock_data: 股票数据
        initial_capital: 初始资金

    Returns:
        dict: 回测结果（包含真实换手额记录）
    """
    # 月末调仓日期（2024年实际交易日）
    rebalance_dates = [
        '2024-01-31',
        '2024-02-29',
        '2024-03-29',
        '2024-04-30',
        '2024-05-31',
        '2024-06-28',
        '2024-07-31',
        '2024-08-30',
        '2024-09-30'
    ]

    # 转换为pandas Timestamp
    rebalance_dates = [pd.Timestamp(d) for d in rebalance_dates]

    holdings_history = []
    turnover_details = []  # 真实换手额记录
    prev_holdings_detail = {}  # 上期持仓明细 {symbol: shares}
    current_value = initial_capital
    total_turnover = 0

    for i, date in enumerate(rebalance_dates):
        # 选股
        selected = select_stocks(stock_data, date)

        if not selected:
            print(f"  ⚠️  {date.strftime('%Y-%m-%d')}: 无股票通过筛选，保持现金")
            holdings_history.append({
                'date': date,
                'stocks': [],
                'count': 0
            })
            # 空仓月份：卖出全部持仓
            if prev_holdings_detail:
                sell_amount = sum(
                    stock_data[symbol].loc[date, 'close'] * shares
                    for symbol, shares in prev_holdings_detail.items()
                    if date in stock_data[symbol].index
                )
                sell_cost = sell_amount * 0.00215  # 0.015%佣金 + 0.1%印花税 + 0.1%滑点
                turnover_details.append({
                    'date': date,
                    'sell_amount': sell_amount,
                    'buy_amount': 0,
                    'sell_cost': sell_cost,
                    'buy_cost': 0,
                    'total_cost': sell_cost
                })
                prev_holdings_detail = {}
            continue

        holdings_history.append({
            'date': date,
            'stocks': selected.copy(),
            'count': len(selected)
        })

        # 计算换手金额
        sell_amount = 0
        buy_amount = 0

        prev_holdings_set = set(prev_holdings_detail.keys())
        curr_holdings_set = set(selected)

        # 卖出：上期持有但本期不持有的股票
        sell_stocks = prev_holdings_set - curr_holdings_set
        for symbol in sell_stocks:
            if date in stock_data[symbol].index:
                shares = prev_holdings_detail[symbol]
                price = stock_data[symbol].loc[date, 'close']
                sell_amount += shares * price

        # 买入：本期持有但上期不持有的股票
        buy_stocks = curr_holdings_set - prev_holdings_set
        capital_per_stock = current_value / len(selected)
        for symbol in buy_stocks:
            buy_amount += capital_per_stock

        # 计算成本
        sell_cost = sell_amount * 0.00215  # 0.015%佣金 + 0.1%印花税 + 0.1%滑点
        buy_cost = buy_amount * 0.00115    # 0.015%佣金 + 0.1%滑点
        total_cost = sell_cost + buy_cost

        turnover_details.append({
            'date': date,
            'sell_amount': sell_amount,
            'buy_amount': buy_amount,
            'sell_cost': sell_cost,
            'buy_cost': buy_cost,
            'total_cost': total_cost
        })

        # 计算换手（第一次不算换手）
        if i > 0:
            prev_holdings = set(holdings_history[i-1]['stocks'])
            curr_holdings = set(selected)
            turnover = len(prev_holdings.symmetric_difference(curr_holdings))
            total_turnover += turnover

        # 更新持仓明细：记录每只股票的持股数
        new_holdings_detail = {}
        capital_per_stock = current_value / len(selected)
        for symbol in selected:
            if date in stock_data[symbol].index:
                price = stock_data[symbol].loc[date, 'close']
                shares = capital_per_stock / price
                new_holdings_detail[symbol] = shares

        prev_holdings_detail = new_holdings_detail

        # 如果不是最后一个调仓日，计算到下一个调仓日的收益
        if i < len(rebalance_dates) - 1:
            next_date = rebalance_dates[i + 1]
            capital_per_stock = current_value / len(selected)
            period_value = 0

            for symbol in selected:
                df = stock_data[symbol]

                if date not in df.index or next_date not in df.index:
                    # 数据缺失，保持原值
                    period_value += capital_per_stock
                    continue

                buy_price = df.loc[date, 'close']
                sell_price = df.loc[next_date, 'close']

                shares = capital_per_stock / buy_price
                period_value += shares * sell_price

            current_value = period_value

    total_return = (current_value - initial_capital) / initial_capital
    turnover_rate = total_turnover / (len(rebalance_dates) * 10) * 100  # 百分比

    return {
        'final_value': current_value,
        'total_return': total_return,
        'turnover': turnover_rate,
        'holdings_history': holdings_history,
        'turnover_details': turnover_details
    }


def print_holdings_history(holdings_history: list):
    """打印月度持仓记录"""
    print("\n" + "="*60)
    print("【动态选股 - 月度调仓记录】")
    print("="*60 + "\n")

    for i, record in enumerate(holdings_history):
        date = record['date'].strftime('%Y-%m-%d')
        stocks = record['stocks']
        count = record['count']

        print(f"{date} 调仓:")

        if count == 0:
            print(f"  无股票选中（现金持有）")
        else:
            print(f"  选中: {count}只")
            for symbol in stocks:
                print(f"    - {symbol}")

        # 显示换仓变化
        if i > 0:
            prev_stocks = set(holdings_history[i-1]['stocks'])
            curr_stocks = set(stocks)

            removed = prev_stocks - curr_stocks
            added = curr_stocks - prev_stocks

            if removed:
                print(f"  换出: {', '.join(removed)}")
            if added:
                print(f"  换入: {', '.join(added)}")
            if not removed and not added:
                print(f"  无变化")

        print()


def print_comparison(fixed_result: dict, dynamic_result: dict):
    """打印对比结果"""
    print("="*60)
    print("【对比结果】")
    print("="*60 + "\n")

    print("场景1 - 固定持仓（10只等权）:")
    print(f"  最终价值: ¥{fixed_result['final_value']:,.2f}")
    print(f"  总收益率: {fixed_result['total_return']*100:.2f}%")
    print(f"  换手率: {fixed_result['turnover']:.2f}%")
    print()

    print("场景2 - 动态选股（月度调仓）:")
    print(f"  最终价值: ¥{dynamic_result['final_value']:,.2f}")
    print(f"  总收益率: {dynamic_result['total_return']*100:.2f}%")
    print(f"  换手率: {dynamic_result['turnover']:.2f}%")

    avg_holdings = np.mean([r['count'] for r in dynamic_result['holdings_history']])
    print(f"  平均持仓: {avg_holdings:.1f}只/月")
    print()

    print("="*60)
    print("【结论】")
    print("="*60 + "\n")

    diff_value = dynamic_result['final_value'] - fixed_result['final_value']
    diff_return = dynamic_result['total_return'] - fixed_result['total_return']

    if diff_return > 0.05:  # 超过5%
        conclusion = "✅ 动态选股显著跑赢固定持仓"
        suggestion = "建议: 继续优化，进入Phase 6B（加入更多因子、扩展股票池）"
    elif diff_return > 0:  # 小幅跑赢
        conclusion = "⚠️  动态选股小幅跑赢固定持仓"
        suggestion = "建议: 加入交易成本计算，评估净收益是否仍为正"
    else:  # 持平或跑输
        conclusion = "❌ 动态选股未能跑赢固定持仓"
        suggestion = "建议: 分析原因（规则过严？样本太小？）或放弃策略"

    print(f"差异: 场景2 vs 场景1")
    print(f"  价值差异: {diff_value:+,.2f} 元")
    print(f"  收益差异: {diff_return*100:+.2f}%")
    print()
    print(conclusion)
    print(suggestion)
    print()


def print_turnover_details(turnover_details: list, initial_capital: float):
    """打印真实换手额逐月明细"""
    print("\n" + "="*80)
    print("【真实换手额 - 逐月明细】")
    print("="*80 + "\n")

    # 表头
    print(f"{'日期':<12} {'卖出金额':>12} {'买入金额':>12} {'卖出成本':>10} {'买入成本':>10} {'合计成本':>10}")
    print("-"*80)

    # 逐月数据
    total_sell = 0
    total_buy = 0
    total_sell_cost = 0
    total_buy_cost = 0
    total_cost = 0

    for detail in turnover_details:
        date_str = detail['date'].strftime('%Y-%m-%d')
        sell_amt = detail['sell_amount']
        buy_amt = detail['buy_amount']
        sell_c = detail['sell_cost']
        buy_c = detail['buy_cost']
        tot_c = detail['total_cost']

        print(f"{date_str:<12} ¥{sell_amt:>10,.0f} ¥{buy_amt:>10,.0f} "
              f"¥{sell_c:>8,.2f} ¥{buy_c:>8,.2f} ¥{tot_c:>8,.2f}")

        total_sell += sell_amt
        total_buy += buy_amt
        total_sell_cost += sell_c
        total_buy_cost += buy_c
        total_cost += tot_c

    print("-"*80)
    print(f"{'总计':<12} ¥{total_sell:>10,.0f} ¥{total_buy:>10,.0f} "
          f"¥{total_sell_cost:>8,.2f} ¥{total_buy_cost:>8,.2f} ¥{total_cost:>8,.2f}")
    print("="*80)


def print_cost_comparison(turnover_details: list, initial_capital: float, dynamic_result: dict, fixed_result: dict):
    """打印成本对比分析"""
    # 计算实际成本
    actual_total_cost = sum(d['total_cost'] for d in turnover_details)
    actual_cost_rate = actual_total_cost / initial_capital

    # 保守估算成本（Phase 6B使用的）
    conservative_cost_rate = 0.0264  # 2.64%

    # 修正后的净收益
    gross_excess_return = dynamic_result['total_return'] - fixed_result['total_return']
    net_excess_return = gross_excess_return - actual_cost_rate

    print("\n" + "="*80)
    print("【成本对比分析】")
    print("="*80 + "\n")

    print("实际交易成本分析:")
    print(f"  实际总成本: ¥{actual_total_cost:,.2f}")
    print(f"  成本率: {actual_cost_rate*100:.2f}%")
    print()

    print("保守估算（Phase 6B）:")
    print(f"  保守成本率: {conservative_cost_rate*100:.2f}%")
    print()

    print("成本对比:")
    print(f"  成本差值: {(actual_cost_rate - conservative_cost_rate)*100:+.2f}%")
    print(f"  实际成本 {'远低于' if actual_cost_rate < conservative_cost_rate * 0.5 else '低于'} 保守估算")
    print()

    print("="*80)
    print("【净超额收益修正】")
    print("="*80 + "\n")

    print(f"毛超额收益: {gross_excess_return*100:+.2f}%")
    print(f"  - 场景2（动态选股）: {dynamic_result['total_return']*100:.2f}%")
    print(f"  - 场景1（固定持仓）: {fixed_result['total_return']*100:.2f}%")
    print()

    print(f"实际交易成本: -{actual_cost_rate*100:.2f}%")
    print()

    print(f"净超额收益: {net_excess_return*100:+.2f}%")
    print()

    if net_excess_return > 0.10:  # >10%
        conclusion = "✅ 扣除实际成本后，动态选股仍显著跑赢固定持仓"
    elif net_excess_return > 0.05:  # 5%-10%
        conclusion = "✅ 扣除实际成本后，动态选股依然跑赢固定持仓"
    elif net_excess_return > 0:  # 0%-5%
        conclusion = "⚠️  扣除实际成本后，动态选股小幅跑赢固定持仓"
    else:
        conclusion = "❌ 扣除实际成本后，动态选股未能跑赢固定持仓"

    print(conclusion)
    print()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Phase 6A-PoC: 动态选股 vs 固定持仓")
    print("="*60 + "\n")

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data(data_dir)

    if not stock_data:
        print("❌ 无法加载数据，请检查数据目录")
        sys.exit(1)

    print()

    # 场景1: 固定持仓
    print("正在回测场景1（固定持仓）...")
    fixed_result = backtest_fixed(stock_data)
    print("✅ 场景1回测完成")
    print()

    # 场景2: 动态选股
    print("正在回测场景2（动态选股）...")
    dynamic_result = backtest_dynamic(stock_data)
    print("✅ 场景2回测完成")

    # 打印月度持仓
    print_holdings_history(dynamic_result['holdings_history'])

    # 打印对比结果
    print_comparison(fixed_result, dynamic_result)

    # 打印真实换手额明细
    initial_capital = 100000
    print_turnover_details(dynamic_result['turnover_details'], initial_capital)

    # 打印成本对比分析
    print_cost_comparison(dynamic_result['turnover_details'], initial_capital, dynamic_result, fixed_result)


if __name__ == "__main__":
    main()
