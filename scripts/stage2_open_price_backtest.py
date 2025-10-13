#!/usr/bin/env python3
"""
Stage 2: 开盘价下单回测

优化策略:
    - 调仓日以开盘价直接下单（省去溢价1% + 缓冲0.5%）
    - 保持止损逻辑不变
    - 统计成交率和实际成本

对比:
    - Baseline: 无止损
    - Variant A: 5%止损
    - Variant B: 10%止损

用法:
    python scripts/stage2_open_price_backtest.py --config stage1_params_aggressive.yaml
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse
from datetime import datetime

try:
    from ruamel.yaml import YAML
    yaml = YAML(typ='safe')
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.simple_matcher import SimpleConservativeMatcher
from backend.basic_orders import StopOrder
from utils.io import (
    ensure_directories,
    save_json_with_metadata,
    load_benchmark_data
)


def load_config(config_name='stage1_params_aggressive.yaml'):
    """加载配置"""
    config_path = Path(__file__).parent.parent / 'config' / config_name

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    if not HAS_YAML:
        print("❌ 请安装 ruamel.yaml")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f)

    print(f"✓ 加载配置: {config_name}")
    return config


def load_stock_pool():
    """加载medium_cap股票池"""
    yaml_path = Path(__file__).parent.parent / 'stock_pool.yaml'

    if not yaml_path.exists():
        print(f"❌ 配置文件不存在: {yaml_path}")
        sys.exit(1)

    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f)

    stock_pools = config.get('stock_pools', {})
    small_cap_stocks = {s['symbol']: s['name'] for s in stock_pools.get('small_cap', [])}
    medium_cap_config = stock_pools.get('medium_cap', {})
    additional_stocks = {s['symbol']: s['name'] for s in medium_cap_config.get('additional', [])}
    stocks = {**small_cap_stocks, **additional_stocks}

    print(f"✓ 加载medium_cap股票池（{len(stocks)}只）")
    return stocks


def load_stock_data(data_dir, start_date, end_date, stock_pool):
    """加载股票数据并计算MA"""
    data = {}

    for symbol, name in stock_pool.items():
        csv_file = Path(data_dir) / f'{symbol}.csv'
        if not csv_file.exists():
            continue

        df = pd.read_csv(csv_file, index_col='date', parse_dates=True)
        df = df[start_date:end_date]

        if df.empty:
            continue

        df['symbol'] = symbol
        df['name'] = name
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()

        data[symbol] = df

    print(f"✓ 加载 {len(data)} 只股票（{start_date} ~ {end_date}）")
    return data


def calculate_20d_return(df, date):
    """计算20日涨幅"""
    try:
        if date not in df.index:
            return np.nan

        date_loc = df.index.get_loc(date)
        if date_loc < 20:
            return np.nan

        current_price = df.loc[date, 'close']
        price_20d_ago = df.iloc[date_loc - 20]['close']

        return (current_price - price_20d_ago) / price_20d_ago
    except:
        return np.nan


def check_ma_crossover(df, date):
    """检查MA5>MA10"""
    try:
        if date not in df.index:
            return False

        ma5 = df.loc[date, 'ma5']
        ma10 = df.loc[date, 'ma10']

        if pd.isna(ma5) or pd.isna(ma10):
            return False

        return ma5 > ma10
    except:
        return False


def select_stocks(stock_data, date, momentum_threshold=0.0, target_count=20):
    """选股规则：20日涨幅>threshold AND MA5>MA10"""
    selected = []

    for symbol, df in stock_data.items():
        ret_20d = calculate_20d_return(df, date)
        if pd.isna(ret_20d) or ret_20d <= momentum_threshold:
            continue

        if not check_ma_crossover(df, date):
            continue

        selected.append(symbol)

    return selected[:target_count]


def backtest_open_price(stock_data, rebalance_dates, config, stop_loss_pct=None):
    """
    回测：开盘价买入 + 止损卖出

    Args:
        stock_data: 股票数据字典
        rebalance_dates: 调仓日期列表
        config: 配置字典
        stop_loss_pct: 止损比例（None表示无止损）

    Returns:
        dict: 回测结果
    """
    # 初始化参数
    initial_capital = config['backtest']['initial_capital']
    target_count = 20
    momentum_threshold = config['strategy']['momentum_threshold']

    # 创建撮合引擎（仅用于止损）
    matcher = SimpleConservativeMatcher(config)

    # 初始化状态
    rebalance_dates = [pd.Timestamp(d) for d in rebalance_dates]
    current_value = initial_capital
    holdings = {}  # {symbol: {'shares': int, 'buy_price': float, 'stop_order': StopOrder}}
    stop_triggered_count = 0
    total_trades = 0
    commission_rate = config['commission']['rate']
    stamp_tax = config['commission']['stamp_tax']
    min_commission = config['commission']['minimum']

    for i, date in enumerate(rebalance_dates):
        # 选股
        selected = select_stocks(stock_data, date, momentum_threshold, target_count)

        if not selected:
            continue

        # 清仓旧持仓（使用收盘价）
        if holdings:
            for symbol, position in holdings.items():
                if symbol in stock_data and date in stock_data[symbol].index:
                    sell_price = stock_data[symbol].loc[date, 'close']
                    proceeds = position['shares'] * sell_price

                    # 计算卖出佣金
                    commission = max(proceeds * commission_rate, min_commission)
                    stamp = proceeds * stamp_tax
                    net_proceeds = proceeds - commission - stamp

                    current_value += net_proceeds
            holdings = {}

        # 建立新仓位（开盘价买入）
        capital_per_stock = current_value / len(selected)

        for symbol in selected:
            df = stock_data[symbol]
            if date not in df.index:
                continue

            # 直接以开盘价买入（无溢价、无缓冲）
            open_price = df.loc[date, 'open']

            # 预估可买股数（100股整数倍）
            quantity = int(capital_per_stock / open_price / 100) * 100
            if quantity < 100:
                continue

            # 计算实际成本
            amount = quantity * open_price
            commission = max(amount * commission_rate, min_commission)
            cost = amount + commission

            current_value -= cost
            total_trades += 1

            # 建立持仓
            holdings[symbol] = {
                'shares': quantity,
                'buy_price': open_price,
                'stop_order': None
            }

            # 设置止损单（如果启用）
            if stop_loss_pct is not None:
                trigger_price = open_price * (1 - stop_loss_pct)
                holdings[symbol]['stop_order'] = StopOrder(
                    symbol=symbol,
                    direction='sell',
                    quantity=quantity,
                    trigger_price=trigger_price
                )

        # 检查止损（在下一调仓期前的每一天）
        if i < len(rebalance_dates) - 1 and stop_loss_pct is not None:
            next_rebalance = rebalance_dates[i + 1]

            for symbol in list(holdings.keys()):
                if symbol not in stock_data:
                    continue

                df = stock_data[symbol]
                position = holdings[symbol]
                stop_order = position['stop_order']

                if stop_order is None:
                    continue

                # 检查每一天是否触发止损
                daily_dates = df[date:next_rebalance].index[1:]

                for check_date in daily_dates:
                    if check_date not in df.index:
                        continue

                    bar = {
                        'date': check_date.strftime('%Y-%m-%d'),
                        'open': df.loc[check_date, 'open'],
                        'high': df.loc[check_date, 'high'],
                        'low': df.loc[check_date, 'low'],
                        'close': df.loc[check_date, 'close'],
                        'volume': df.loc[check_date, 'volume'],
                        'prev_close': df.loc[check_date]['close'] if check_date > df.index[0] else df.loc[check_date, 'open']
                    }

                    # 尝试撮合止损单
                    trade = matcher.match_stop(stop_order, bar)

                    if trade:
                        # 止损触发
                        proceeds = trade.amount - trade.commission
                        current_value += proceeds
                        stop_triggered_count += 1
                        total_trades += 1

                        # 移除持仓
                        del holdings[symbol]
                        break

    # 清仓（使用最后一天收盘价）
    final_date = rebalance_dates[-1]
    for symbol, position in holdings.items():
        if symbol in stock_data and final_date in stock_data[symbol].index:
            sell_price = stock_data[symbol].loc[final_date, 'close']
            proceeds = position['shares'] * sell_price

            commission = max(proceeds * commission_rate, min_commission)
            stamp = proceeds * stamp_tax
            net_proceeds = proceeds - commission - stamp

            current_value += net_proceeds

    # 计算收益
    total_return = (current_value - initial_capital) / initial_capital
    stop_trigger_rate = (stop_triggered_count / total_trades * 100) if total_trades > 0 else 0

    return {
        'final_value': current_value,
        'total_return': total_return,
        'stop_triggered': stop_triggered_count,
        'total_trades': total_trades,
        'stop_trigger_rate': stop_trigger_rate
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Stage 2: 开盘价下单回测')
    parser.add_argument(
        '--config',
        type=str,
        default='stage1_params_aggressive.yaml',
        help='配置文件名'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Stage 2: 开盘价下单回测")
    print("=" * 60)
    print()

    # 初始化
    ensure_directories()
    config = load_config(args.config)
    stock_pool = load_stock_pool()

    # 加载数据（2024年）
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    start_date = '2024-01-01'
    end_date = '2024-09-30'

    print(f"\n加载数据: {start_date} ~ {end_date}")
    stock_data = load_stock_data(data_dir, start_date, end_date, stock_pool)

    # 调仓日期
    rebalance_dates = [
        '2024-01-31', '2024-02-29', '2024-03-29', '2024-04-30',
        '2024-05-31', '2024-06-28', '2024-07-31', '2024-08-30',
        '2024-09-30'
    ]

    # 加载沪深300基准
    print("\n加载沪深300基准...")
    benchmark_df = load_benchmark_data(start_date='2024-01-01')
    benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
    benchmark_2024 = benchmark_df[(benchmark_df['date'] >= '2024-01-01') &
                                   (benchmark_df['date'] <= '2024-09-30')]

    start_price = benchmark_2024.iloc[0]['close']
    end_price = benchmark_2024.iloc[-1]['close']
    hs300_return = (end_price - start_price) / start_price

    print(f"✓ 沪深300收益: {hs300_return*100:.2f}%")

    # 执行回测
    print("\n" + "=" * 60)
    print("执行回测（开盘价下单）")
    print("=" * 60)

    # Baseline: 无止损
    print("\n[1/3] Baseline: 无止损")
    baseline_result = backtest_open_price(stock_data, rebalance_dates, config, stop_loss_pct=None)
    print(f"✓ 收益: {baseline_result['total_return']*100:.2f}%")

    # Variant A: 5%止损
    print("\n[2/3] Variant A: 5%止损")
    variant_a_result = backtest_open_price(stock_data, rebalance_dates, config, stop_loss_pct=0.05)
    print(f"✓ 收益: {variant_a_result['total_return']*100:.2f}%")
    print(f"✓ 止损触发: {variant_a_result['stop_triggered']}次 / {variant_a_result['total_trades']}笔")

    # Variant B: 10%止损
    print("\n[3/3] Variant B: 10%止损")
    variant_b_result = backtest_open_price(stock_data, rebalance_dates, config, stop_loss_pct=0.10)
    print(f"✓ 收益: {variant_b_result['total_return']*100:.2f}%")
    print(f"✓ 止损触发: {variant_b_result['stop_triggered']}次 / {variant_b_result['total_trades']}笔")

    # 汇总结果
    results = {
        'baseline': {
            'total_return': baseline_result['total_return'],
            'final_value': baseline_result['final_value'],
            'description': '无止损（开盘价下单）'
        },
        'variant_a': {
            'total_return': variant_a_result['total_return'],
            'final_value': variant_a_result['final_value'],
            'stop_triggered': variant_a_result['stop_triggered'],
            'total_trades': variant_a_result['total_trades'],
            'stop_trigger_rate': variant_a_result['stop_trigger_rate'],
            'description': '5%止损（开盘价下单）'
        },
        'variant_b': {
            'total_return': variant_b_result['total_return'],
            'final_value': variant_b_result['final_value'],
            'stop_triggered': variant_b_result['stop_triggered'],
            'total_trades': variant_b_result['total_trades'],
            'stop_trigger_rate': variant_b_result['stop_trigger_rate'],
            'description': '10%止损（开盘价下单）'
        },
        'benchmark': {
            'hs300_return': hs300_return,
            'description': '沪深300指数'
        },
        'config': {
            'year': 2024,
            'stock_count': 20,
            'rebalance_freq': 'monthly',
            'entry_method': 'open_price',  # 开盘价下单
            'stop_slippage': config['matching']['stop_slippage'],
            'limit_buffer': config['matching']['limit_buffer']
        }
    }

    # 打印对比
    print("\n" + "=" * 60)
    print("对比摘要")
    print("=" * 60)
    print(f"\n{'策略':<25} {'收益':<10} {'vs基准':<10} {'止损触发率':<10}")
    print("-" * 65)

    print(f"{'Baseline (开盘价)':<25} {baseline_result['total_return']*100:>6.2f}% {(baseline_result['total_return']-hs300_return)*100:>+6.2f}% {'N/A':<10}")
    print(f"{'Variant A (5%止损)':<25} {variant_a_result['total_return']*100:>6.2f}% {(variant_a_result['total_return']-hs300_return)*100:>+6.2f}% {variant_a_result['stop_trigger_rate']:>6.1f}%")
    print(f"{'Variant B (10%止损)':<25} {variant_b_result['total_return']*100:>6.2f}% {(variant_b_result['total_return']-hs300_return)*100:>+6.2f}% {variant_b_result['stop_trigger_rate']:>6.1f}%")
    print(f"{'沪深300':<25} {hs300_return*100:>6.2f}% {'0.00%':<10} {'N/A':<10}")
    print()

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_json_with_metadata(
        data=results,
        filepath=f'results/stage2_open_price_backtest_{timestamp}.json',
        phase='Stage 2 Priority 1.2',
        version='2.0.0'
    )

    print(f"✓ 结果已保存: results/stage2_open_price_backtest_{timestamp}.json")
    print()

    # 结论
    print("=" * 60)
    print("结论")
    print("=" * 60)

    target_return = 0.35  # 35%目标（优先级1验收标准）

    if baseline_result['total_return'] >= target_return:
        print(f"✅ 通过: Baseline达到{baseline_result['total_return']*100:.2f}% (目标≥35%)")
        print("   → 可进入优先级2：市场状态驱动止损")
    else:
        print(f"⚠️ 接近目标: Baseline仅{baseline_result['total_return']*100:.2f}% (目标≥35%)")
        print(f"   → 继续评估成本优化效果")

    print()


if __name__ == '__main__':
    main()
