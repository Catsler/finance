#!/usr/bin/env python3
"""
Stage 2 优先级2：市场状态驱动止损回测

策略:
    - 调仓日识别市场状态（牛/熊/震荡）
    - 根据市场状态动态设置止损比例
    - 开盘价直接买入（继承优先级1）
    - 统计各市场状态下的止损效果

用法:
    python scripts/stage2_dynamic_stop_backtest.py --year 2024
    python scripts/stage2_dynamic_stop_backtest.py --year 2023
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse
from datetime import datetime
from collections import defaultdict

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
from utils.market_regime import identify_market_regime, get_regime_statistics


def load_config(config_name='stage2_dynamic_stop.yaml'):
    """加载Stage 2动态止损配置"""
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


def backtest_dynamic_stop(stock_data, hs300_data, rebalance_dates, config):
    """
    动态止损回测

    Args:
        stock_data: 股票数据字典
        hs300_data: HS300数据DataFrame
        rebalance_dates: 调仓日期列表
        config: 配置字典

    Returns:
        dict: 回测结果
    """
    # 初始化参数
    initial_capital = config['backtest']['initial_capital']
    target_count = 20
    momentum_threshold = config['strategy']['momentum_threshold']

    # 动态止损参数
    regime_params = config['regime_detection']
    stop_loss_mapping = config['market_driven_stop_loss']

    # 创建撮合引擎（仅用于止损）
    matcher = SimpleConservativeMatcher(config)

    # 初始化状态
    rebalance_dates = [pd.Timestamp(d) for d in rebalance_dates]
    current_value = initial_capital
    holdings = {}
    commission_rate = config['commission']['rate']
    stamp_tax = config['commission']['stamp_tax']
    min_commission = config['commission']['minimum']

    # 统计数据
    regime_distribution = defaultdict(int)
    stop_by_regime = defaultdict(lambda: {'triggered': 0, 'total': 0})
    total_trades = 0

    for i, date in enumerate(rebalance_dates):
        # 识别市场状态
        regime = identify_market_regime(
            hs300_data,
            date,
            momentum_bull_threshold=regime_params['momentum_bull_threshold'],
            momentum_bear_threshold=regime_params['momentum_bear_threshold'],
            volatility_threshold=regime_params['volatility_threshold']
        )

        regime_distribution[regime] += 1

        # 根据市场状态选择止损比例
        stop_loss_pct = stop_loss_mapping[f'{regime}_market']['stop_loss_pct']

        print(f"  {date.strftime('%Y-%m-%d')}: {regime.upper()} market → 止损{stop_loss_pct*100:.0f}%")

        # 选股
        selected = select_stocks(stock_data, date, momentum_threshold, target_count)

        if not selected:
            continue

        # 清仓旧持仓
        if holdings:
            for symbol, position in holdings.items():
                if symbol in stock_data and date in stock_data[symbol].index:
                    sell_price = stock_data[symbol].loc[date, 'close']
                    proceeds = position['shares'] * sell_price

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

            # 开盘价买入
            open_price = df.loc[date, 'open']

            quantity = int(capital_per_stock / open_price / 100) * 100
            if quantity < 100:
                continue

            amount = quantity * open_price
            commission = max(amount * commission_rate, min_commission)
            cost = amount + commission

            current_value -= cost
            total_trades += 1

            # 建立持仓
            holdings[symbol] = {
                'shares': quantity,
                'buy_price': open_price,
                'regime': regime,  # 记录买入时的市场状态
                'stop_order': None
            }

            # 设置止损单（动态止损比例）
            trigger_price = open_price * (1 - stop_loss_pct)
            holdings[symbol]['stop_order'] = StopOrder(
                symbol=symbol,
                direction='sell',
                quantity=quantity,
                trigger_price=trigger_price
            )

            stop_by_regime[regime]['total'] += 1

        # 检查止损（在下一调仓期前的每一天）
        if i < len(rebalance_dates) - 1:
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

                    trade = matcher.match_stop(stop_order, bar)

                    if trade:
                        # 止损触发
                        proceeds = trade.amount - trade.commission
                        current_value += proceeds
                        total_trades += 1

                        # 记录止损触发
                        stop_by_regime[position['regime']]['triggered'] += 1

                        # 移除持仓
                        del holdings[symbol]
                        break

    # 清仓
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

    # 计算各市场状态下的止损触发率
    stop_trigger_rates = {}
    for regime, counts in stop_by_regime.items():
        if counts['total'] > 0:
            stop_trigger_rates[f'{regime}_market'] = counts['triggered'] / counts['total'] * 100
        else:
            stop_trigger_rates[f'{regime}_market'] = 0.0

    # 整体止损触发率
    total_stops = sum(counts['triggered'] for counts in stop_by_regime.values())
    overall_stop_rate = total_stops / total_trades * 100 if total_trades > 0 else 0

    return {
        'final_value': current_value,
        'total_return': total_return,
        'stop_triggered': total_stops,
        'total_trades': total_trades,
        'stop_trigger_rate': overall_stop_rate,
        'regime_distribution': dict(regime_distribution),
        'stop_loss_by_regime': stop_trigger_rates
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Stage 2: 市场状态驱动止损回测')
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        choices=[2023, 2024],
        help='测试年份（2023=震荡市, 2024=牛市）'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Stage 2 优先级2：市场状态驱动止损回测")
    print("=" * 60)
    print()

    # 初始化
    ensure_directories()
    config = load_config()
    stock_pool = load_stock_pool()

    # 根据年份设置日期范围
    if args.year == 2024:
        start_date = '2024-01-01'
        end_date = '2024-09-30'
        rebalance_dates = [
            '2024-01-31', '2024-02-29', '2024-03-29', '2024-04-30',
            '2024-05-31', '2024-06-28', '2024-07-31', '2024-08-30',
            '2024-09-30'
        ]
    else:  # 2023
        start_date = '2023-01-01'
        end_date = '2023-12-31'
        rebalance_dates = [
            '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-28',
            '2023-05-31', '2023-06-30', '2023-07-31', '2023-08-31',
            '2023-09-28', '2023-10-31', '2023-11-30', '2023-12-29'
        ]

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    print(f"\n加载数据: {start_date} ~ {end_date}")
    stock_data = load_stock_data(data_dir, start_date, end_date, stock_pool)

    # 加载HS300基准
    print("\n加载HS300基准...")
    benchmark_df = load_benchmark_data(start_date=start_date)
    benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
    benchmark_year = benchmark_df[(benchmark_df['date'] >= start_date) &
                                   (benchmark_df['date'] <= end_date)]

    start_price = benchmark_year.iloc[0]['close']
    end_price = benchmark_year.iloc[-1]['close']
    hs300_return = (end_price - start_price) / start_price

    print(f"✓ 沪深300收益: {hs300_return*100:.2f}%")

    # 执行回测
    print("\n" + "=" * 60)
    print(f"执行回测（{args.year}年 - 动态止损）")
    print("=" * 60)
    print()

    result = backtest_dynamic_stop(stock_data, benchmark_df, rebalance_dates, config)

    print(f"\n✓ 最终收益: {result['total_return']*100:.2f}%")
    print(f"✓ 止损触发: {result['stop_triggered']}次 / {result['total_trades']}笔 ({result['stop_trigger_rate']:.1f}%)")

    # 打印市场状态分布
    print("\n市场状态分布:")
    regime_stats = get_regime_statistics({str(i): regime for i, regime in enumerate(result['regime_distribution'])})
    for regime, count in result['regime_distribution'].items():
        print(f"  {regime.upper()}: {count}个月")

    # 打印各状态下止损触发率
    print("\n各市场状态下止损触发率:")
    for regime, rate in result['stop_loss_by_regime'].items():
        print(f"  {regime}: {rate:.1f}%")

    # 汇总结果
    results = {
        'total_return': result['total_return'],
        'final_value': result['final_value'],
        'stop_triggered': result['stop_triggered'],
        'total_trades': result['total_trades'],
        'stop_trigger_rate': result['stop_trigger_rate'],
        'regime_distribution': result['regime_distribution'],
        'stop_loss_by_regime': result['stop_loss_by_regime'],
        'benchmark': {
            'hs300_return': hs300_return,
            'description': '沪深300指数'
        },
        'config': {
            'year': args.year,
            'stock_count': 20,
            'rebalance_freq': 'monthly',
            'entry_method': 'open_price',
            'stop_loss_mode': 'dynamic',
            'regime_detection': config['regime_detection'],
            'stop_loss_mapping': {k: v['stop_loss_pct'] for k, v in config['market_driven_stop_loss'].items()}
        }
    }

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_json_with_metadata(
        data=results,
        filepath=f'results/stage2_dynamic_{args.year}_{timestamp}.json',
        phase=f'Stage 2 Priority 2 - {args.year}',
        version='2.0.0'
    )

    print(f"\n✓ 结果已保存: results/stage2_dynamic_{args.year}_{timestamp}.json")

    # 验收判断
    print("\n" + "=" * 60)
    print("验收判断")
    print("=" * 60)

    if args.year == 2024:
        criteria = config['acceptance_criteria']['year_2024']
        target = criteria['target_return']
        max_stop_rate = criteria['max_stop_trigger_rate']
        min_alpha = criteria['min_alpha_vs_hs300']

        passed = []
        failed = []

        if result['total_return'] >= target:
            passed.append(f"✅ 收益达标: {result['total_return']*100:.2f}% ≥ {target*100:.0f}%")
        else:
            failed.append(f"❌ 收益未达标: {result['total_return']*100:.2f}% < {target*100:.0f}%")

        if result['stop_trigger_rate'] / 100 <= max_stop_rate:
            passed.append(f"✅ 止损率达标: {result['stop_trigger_rate']:.1f}% ≤ {max_stop_rate*100:.0f}%")
        else:
            failed.append(f"❌ 止损率未达标: {result['stop_trigger_rate']:.1f}% > {max_stop_rate*100:.0f}%")

        alpha = result['total_return'] - hs300_return
        if alpha >= min_alpha:
            passed.append(f"✅ Alpha达标: +{alpha*100:.2f}% ≥ +{min_alpha*100:.0f}%")
        else:
            failed.append(f"❌ Alpha未达标: +{alpha*100:.2f}% < +{min_alpha*100:.0f}%")

    else:  # 2023
        criteria = config['acceptance_criteria']['year_2023']
        target = criteria['target_return']
        min_alpha = criteria['min_alpha_vs_hs300']

        passed = []
        failed = []

        if result['total_return'] > target:
            passed.append(f"✅ 收益达标: {result['total_return']*100:.2f}% > {target*100:.0f}%")
        else:
            failed.append(f"❌ 收益未达标: {result['total_return']*100:.2f}% ≤ {target*100:.0f}%")

        alpha = result['total_return'] - hs300_return
        if alpha > min_alpha:
            passed.append(f"✅ Alpha达标: +{alpha*100:.2f}% > +{min_alpha*100:.0f}%")
        else:
            failed.append(f"❌ Alpha未达标: +{alpha*100:.2f}% ≤ +{min_alpha*100:.0f}%")

    print()
    for item in passed:
        print(item)
    for item in failed:
        print(item)

    if not failed:
        print(f"\n✅ {args.year}年验收通过")
    else:
        print(f"\n⚠️ {args.year}年验收未完全通过")

    print()


if __name__ == '__main__':
    main()
