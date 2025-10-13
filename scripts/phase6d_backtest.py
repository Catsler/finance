#!/usr/bin/env python3
"""
Phase 6D: 三年稳健性验证（2022/2023/2024）

⚠️ 注意：
- Sharpe比率计算已移除（原因：之前使用硬编码波动率0.15，不可靠）
- 当前输出仅包含：总收益、年化收益、换手率、超额收益
- 如需真实Sharpe，需重构为日度回测并计算实际波动率

目标:
    验证MA5/MA10+双重止损+动态选股策略在2022/2023/2024三年的稳健性

策略:
    - 动态选股：每月月末筛选（20日涨幅>0% AND MA5>MA10）
    - 固定持仓：10只等权持有
    - 沪深300基准

用法:
    python scripts/phase6d_backtest.py --year 2022
    python scripts/phase6d_backtest.py --full  # 默认20只股票池（推荐）
    python scripts/phase6d_backtest.py --full --pool small_cap  # 10只池（legacy）
    python scripts/phase6d_backtest.py --full --momentum-threshold -5.0  # 参数化测试
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import subprocess
import argparse
from datetime import datetime

# 导入工具模块
sys.path.append(str(Path(__file__).parent.parent))
from utils.io import (
    ensure_directories,
    save_json_with_metadata,
    load_benchmark_data
)


# ===== 配置区（阈值常量）=====
THRESHOLDS = {
    'return_min_2022': -0.20,       # 2022年收益下限（红线）
    'excess_acceleration': 0.10     # 超额收益加速阈值（10%/年）
}


def derive_target_count(pool_name, pool_stocks, cli_value=None):
    """
    统一推导target_count（复用现有规则）

    优先级：CLI参数 > 池名规则 > 池大小
    """
    if cli_value is not None:
        return cli_value

    # 池名规则（与现有行为完全一致）
    if pool_name == 'small_cap':
        return 10
    elif pool_name == 'medium_cap':
        return 20
    elif pool_name == 'legacy_7stocks':
        return 7
    else:
        # 默认：使用池大小
        return len(pool_stocks)


def build_custom_config(start_date, end_date, pool_name, pool_stocks,
                       freq='M', target_count=None):
    """
    构建自定义时间区间配置（pilot模式）

    Args:
        start_date: 起始日期 (str, 'YYYY-MM-DD')
        end_date: 结束日期 (str, 'YYYY-MM-DD')
        pool_name: 股票池名称
        pool_stocks: 股票池数据
        freq: 调仓频率 ('M'=月末, 'Q'=季末)
        target_count: CLI指定的持仓数（可选）

    Returns:
        dict: 配置字典
    """
    # 日期校验
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    if start >= end:
        raise ValueError(f"Invalid date range: {start_date} >= {end_date}")

    # 推导target_count（复用统一逻辑）
    target_count = derive_target_count(pool_name, pool_stocks, target_count)

    # 生成调仓日期（月末）
    rebalance_dates = pd.date_range(start, end, freq=freq).strftime('%Y-%m-%d').tolist()

    return {
        'start_date': start_date,
        'end_date': end_date,
        'rebalance_dates': rebalance_dates,
        'target_count': target_count
    }


def load_stock_pool_from_yaml(pool_name='small_cap'):
    """
    从stock_pool.yaml或stock_pool_legacy7.yaml加载股票池

    Args:
        pool_name: 股票池名称（small_cap/medium_cap/legacy_7stocks）

    Returns:
        dict: {symbol: name}
    """
    try:
        from ruamel.yaml import YAML
    except ImportError:
        print("❌ 请安装 ruamel.yaml: pip install ruamel.yaml")
        sys.exit(1)

    # 根据池名选择配置文件
    if pool_name == 'legacy_7stocks':
        yaml_path = Path(__file__).parent.parent / 'stock_pool_legacy7.yaml'
    else:
        yaml_path = Path(__file__).parent.parent / 'stock_pool.yaml'

    if not yaml_path.exists():
        print(f"❌ 配置文件不存在: {yaml_path}")
        sys.exit(1)

    yaml = YAML(typ='safe')
    with open(yaml_path) as f:
        config = yaml.load(f)

    stock_pools = config.get('stock_pools', {})

    if pool_name == 'small_cap':
        # 直接返回small_cap列表
        stocks = {s['symbol']: s['name'] for s in stock_pools.get('small_cap', [])}
    elif pool_name == 'medium_cap':
        # medium_cap = small_cap + additional
        small_cap_stocks = {s['symbol']: s['name'] for s in stock_pools.get('small_cap', [])}
        medium_cap_config = stock_pools.get('medium_cap', {})
        additional_stocks = {s['symbol']: s['name'] for s in medium_cap_config.get('additional', [])}
        stocks = {**small_cap_stocks, **additional_stocks}
    elif pool_name == 'legacy_7stocks':
        # Phase 8: 7只老股（2005年就存在）
        stocks = {s['symbol']: s['name'] for s in stock_pools.get('legacy_7stocks', [])}
    elif pool_name in stock_pools and isinstance(stock_pools[pool_name], list):
        # Phase 8.1: 支持其他简单列表池（如legacy_test_pool）
        stocks = {s['symbol']: s['name'] for s in stock_pools[pool_name]}
    else:
        print(f"❌ 未知股票池: {pool_name}")
        sys.exit(1)

    yaml_file = 'stock_pool_legacy7.yaml' if pool_name == 'legacy_7stocks' else 'stock_pool.yaml'
    print(f"✓ 从{yaml_file}加载 {pool_name}（{len(stocks)}只股票）")
    return stocks


def get_year_config(year, rebalance_freq='monthly'):
    """
    获取年份配置（起止日期、调仓日期）

    Args:
        year: 年份（2007/2019/2021/2022/2023/2024/2025，Phase 8扩展）
        rebalance_freq: 调仓频率（'monthly' 或 'quarterly'）

    Returns:
        dict: 配置信息
    """
    configs = {
        '2007': {
            'start_date': '2007-01-04',
            'end_date': '2007-12-31',
            'rebalance_dates': [
                '2007-01-31', '2007-02-28', '2007-03-30', '2007-04-30',
                '2007-05-31', '2007-06-29', '2007-07-31', '2007-08-31',
                '2007-09-28', '2007-10-31', '2007-11-30', '2007-12-31'
            ] if rebalance_freq == 'monthly' else [
                '2007-03-30', '2007-06-29', '2007-09-28', '2007-12-31'
            ]
        },
        '2019': {
            'start_date': '2019-01-01',
            'end_date': '2019-12-31',
            'rebalance_dates': [
                '2019-01-31', '2019-02-28', '2019-03-29', '2019-04-30',
                '2019-05-31', '2019-06-28', '2019-07-31', '2019-08-30',
                '2019-09-30', '2019-10-31', '2019-11-29', '2019-12-31'
            ] if rebalance_freq == 'monthly' else [
                '2019-03-29', '2019-06-28', '2019-09-30', '2019-12-31'
            ]
        },
        '2021': {
            'start_date': '2021-01-01',
            'end_date': '2021-12-31',
            'rebalance_dates': [
                '2021-01-29', '2021-02-26', '2021-03-31', '2021-04-30',
                '2021-05-31', '2021-06-30', '2021-07-30', '2021-08-31',
                '2021-09-30', '2021-10-29', '2021-11-30', '2021-12-31'
            ] if rebalance_freq == 'monthly' else [
                '2021-03-31', '2021-06-30', '2021-09-30', '2021-12-31'
            ]
        },
        '2022': {
            'start_date': '2022-01-01',
            'end_date': '2022-12-31',
            'rebalance_dates': [
                '2022-01-28', '2022-02-28', '2022-03-31', '2022-04-29',
                '2022-05-31', '2022-06-30', '2022-07-29', '2022-08-31',
                '2022-09-30', '2022-10-31', '2022-11-30', '2022-12-30'
            ] if rebalance_freq == 'monthly' else [
                '2022-03-31', '2022-06-30', '2022-09-30', '2022-12-30'
            ]
        },
        '2023': {
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'rebalance_dates': [
                '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-28',
                '2023-05-31', '2023-06-30', '2023-07-31', '2023-08-31',
                '2023-09-28', '2023-10-31', '2023-11-30', '2023-12-29'
            ] if rebalance_freq == 'monthly' else [
                '2023-03-31', '2023-06-30', '2023-09-28', '2023-12-29'
            ]
        },
        '2024': {
            'start_date': '2024-01-01',
            'end_date': '2024-09-30',
            'rebalance_dates': [
                '2024-01-31', '2024-02-29', '2024-03-29', '2024-04-30',
                '2024-05-31', '2024-06-28', '2024-07-31', '2024-08-30',
                '2024-09-30'
            ] if rebalance_freq == 'monthly' else [
                '2024-03-29', '2024-06-28', '2024-09-30'
            ]
        },
        '2025': {
            'start_date': '2025-01-01',
            'end_date': '2025-09-30',
            'rebalance_dates': [
                '2025-01-31', '2025-02-28', '2025-03-31', '2025-04-30',
                '2025-05-30', '2025-06-30', '2025-07-31', '2025-08-29',
                '2025-09-30'
            ] if rebalance_freq == 'monthly' else [
                '2025-03-31', '2025-06-30', '2025-09-30'
            ]
        }
    }

    return configs.get(year)


def load_stock_data(data_dir, start_date, end_date, pool_name='small_cap'):
    """
    加载股票数据

    Args:
        data_dir: 数据目录
        start_date: 起始日期
        end_date: 结束日期
        pool_name: 股票池名称（small_cap/medium_cap）

    Returns:
        dict: {symbol: DataFrame}
    """
    stocks = load_stock_pool_from_yaml(pool_name)

    data = {}
    for symbol, name in stocks.items():
        csv_file = Path(data_dir) / f'{symbol}.csv'
        if not csv_file.exists():
            print(f"❌ 文件不存在: {csv_file}")
            continue

        df = pd.read_csv(csv_file, index_col='date', parse_dates=True)
        df = df[start_date:end_date]

        if df.empty:
            print(f"⚠️ {symbol} 在 {start_date} ~ {end_date} 无可用数据，已跳过")
            continue

        df['symbol'] = symbol
        df['name'] = name

        # 计算MA5和MA10
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


def select_stocks(stock_data, date, momentum_threshold=0.0):
    """
    选股规则：20日涨幅>threshold AND MA5>MA10

    Args:
        stock_data: 股票数据字典
        date: 选股日期
        momentum_threshold: 20日涨幅阈值（百分比，如-5.0表示-5%）

    Returns:
        list: 满足条件的股票代码列表
    """
    selected = []
    threshold_decimal = momentum_threshold / 100  # 转换为小数

    for symbol, df in stock_data.items():
        ret_20d = calculate_20d_return(df, date)
        if pd.isna(ret_20d) or ret_20d <= threshold_decimal:
            continue

        if not check_ma_crossover(df, date):
            continue

        selected.append(symbol)

    return selected


def select_stocks_with_stability(stock_data, date, prev_holdings, momentum_threshold=0.0, stability_ratio=0.5, target_count=20, debug=False):
    """
    持仓稳定性选股：优先保留仍满足条件的旧仓位

    Args:
        stock_data: 股票数据字典
        date: 选股日期
        prev_holdings: 上期持仓列表
        momentum_threshold: 20日涨幅阈值（百分比）
        stability_ratio: 保留比例（0.5 = 优先保留50%老仓位）
        target_count: 目标持仓数量
        debug: 是否启用DEBUG日志

    Returns:
        list: 选中的股票列表
    """
    # Step 1: 筛选当前满足条件的所有股票
    all_qualified = select_stocks(stock_data, date, momentum_threshold)
    if debug:
        print(f"[DEBUG] {date.date()}: 满足条件股票数={len(all_qualified)}")

    if not prev_holdings:
        # 首次建仓，按原逻辑，但限制数量
        actual_target = min(target_count, len(all_qualified))
        if debug:
            print(f"[DEBUG] {date.date()}: 首次建仓，选取{actual_target}只")
        return all_qualified[:actual_target]

    # Step 2: 找出"既在旧仓位又满足当前条件"的股票
    old_still_qualified = [s for s in prev_holdings if s in all_qualified]

    # Step 3: 动态调整target_count（不超过实际满足条件的数量）
    actual_target = min(target_count, len(all_qualified))

    # Step 4: 计算保留数量
    keep_count = min(
        len(old_still_qualified),  # 不能超过实际可保留数量
        int(actual_target * stability_ratio)  # 目标保留比例
    )

    # Step 5: 保留老仓位（按原持仓顺序）
    keep_stocks = old_still_qualified[:keep_count]

    # Step 6: 补充新股票
    new_candidates = [s for s in all_qualified if s not in keep_stocks]
    new_stocks = new_candidates[:actual_target - len(keep_stocks)]

    # [DEBUG LOG]
    if debug:
        print(f"[DEBUG] {date.date()}: 旧仓{len(prev_holdings)}只, 仍合格{len(old_still_qualified)}只, "
              f"保留{keep_count}只(ratio={stability_ratio}), 补充新股{len(new_stocks)}只")
        if keep_stocks:
            print(f"[DEBUG] 保留: {keep_stocks[:3]}{'...' if len(keep_stocks) > 3 else ''}")
        if new_stocks:
            print(f"[DEBUG] 新增: {new_stocks[:3]}{'...' if len(new_stocks) > 3 else ''}")

    # Step 7: 合并
    final_selection = keep_stocks + new_stocks

    # [ENHANCED DEBUG LOG] 调仓摘要（Phase 8专用）
    if debug and prev_holdings:
        removed = [s for s in prev_holdings if s not in final_selection]
        added = [s for s in final_selection if s not in prev_holdings]
        turnover_rate = (len(removed) / len(prev_holdings)) * 100 if prev_holdings else 0

        print(f"\n[调仓摘要] {date.date()}")
        print(f"  持仓: {len(prev_holdings)}只 → {len(final_selection)}只")
        print(f"  换出: {len(removed)}只 - {removed if removed else '无'}")
        print(f"  换入: {len(added)}只 - {added if added else '无'}")
        print(f"  换手率: {turnover_rate:.1f}%")

    return final_selection


def calculate_sharpe_ratio(returns, risk_free_rate=0.03):
    """
    计算Sharpe比率

    Args:
        returns: 日收益率序列
        risk_free_rate: 无风险利率（年化）

    Returns:
        float: Sharpe比率
    """
    if len(returns) == 0:
        return 0.0

    # 日均超额收益
    daily_rf = risk_free_rate / 252
    excess_returns = returns - daily_rf

    # 年化
    mean_excess = excess_returns.mean() * 252
    std = returns.std() * np.sqrt(252)

    if std == 0:
        return 0.0

    return mean_excess / std


def backtest_fixed(stock_data, initial_capital=100000, commission=0.0):
    """固定持仓回测"""
    # 扣除初始买入成本
    available_capital = initial_capital * (1 - commission) if commission > 0 else initial_capital
    capital_per_stock = available_capital / len(stock_data)
    total_value = 0

    for symbol, df in stock_data.items():
        buy_price = df.iloc[0]['close']
        sell_price = df.iloc[-1]['close']

        shares = capital_per_stock / buy_price
        stock_value = shares * sell_price
        # 扣除卖出成本
        if commission > 0:
            stock_value *= (1 - commission)
        total_value += stock_value

    total_return = (total_value - initial_capital) / initial_capital

    return {
        'final_value': total_value,
        'total_return': total_return,
        'turnover': 0
    }


def backtest_dynamic(stock_data, rebalance_dates, initial_capital=100000, momentum_threshold=0.0, commission=0.0, stability_ratio=0.0, target_count=20, take_profit_tiers=None, debug=False):
    """
    动态选股回测

    Args:
        stock_data: 股票数据字典
        rebalance_dates: 调仓日期列表
        initial_capital: 初始资金
        momentum_threshold: 20日涨幅阈值（百分比）
        commission: 单边交易佣金率（例如0.001表示0.1%）
        stability_ratio: 持仓稳定性比例（0=关闭，0.5=优先保留50%老仓位）
        target_count: 目标持仓数量
        take_profit_tiers: 止盈梯度列表（例如[0.10, 0.15]表示10%和15%），None表示关闭
        debug: 是否启用DEBUG日志

    Returns:
        dict: 回测结果
    """
    # [DEBUG LOG]
    if debug:
        take_profit_str = f", take_profit_tiers={take_profit_tiers}" if take_profit_tiers else ""
        print(f"[DEBUG] backtest_dynamic called: stability_ratio={stability_ratio}, target_count={target_count}, "
              f"commission={commission}, periods={len(rebalance_dates)}{take_profit_str}")

    rebalance_dates = [pd.Timestamp(d) for d in rebalance_dates]

    holdings_history = []
    current_value = initial_capital
    total_turnover = 0
    take_profit_triggers = []  # 止盈触发记录

    for i, date in enumerate(rebalance_dates):
        # 选股：根据stability_ratio决定是否使用持仓稳定性过滤
        if stability_ratio > 0 and i > 0:
            prev_holdings = holdings_history[i-1]['stocks']
            selected = select_stocks_with_stability(
                stock_data, date, prev_holdings, momentum_threshold, stability_ratio, target_count, debug
            )
        else:
            selected = select_stocks(stock_data, date, momentum_threshold)
            # 限制数量
            if target_count > 0:
                selected = selected[:target_count]

        if not selected:
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

        # [ENHANCED DEBUG] 调仓摘要（Phase 8）
        if debug and i > 0:
            prev_stocks = holdings_history[i-1]['stocks']
            removed = [s for s in prev_stocks if s not in selected]
            added = [s for s in selected if s not in prev_stocks]
            turnover_rate = (len(removed) / len(prev_stocks)) * 100 if prev_stocks else 0

            print(f"\n[调仓摘要] {date.date()}")
            print(f"  持仓: {len(prev_stocks)}只 → {len(selected)}只")
            print(f"  换出: {len(removed)}只 - {removed if removed else '无'}")
            print(f"  换入: {len(added)}只 - {added if added else '无'}")
            print(f"  换手率: {turnover_rate:.1f}%")
        elif debug and i == 0:
            print(f"\n[首次建仓] {date.date()}: {len(selected)}只 - {selected}")

        # 初始建仓成本
        if i == 0 and commission > 0:
            initial_trade_cost = current_value * commission
            current_value -= initial_trade_cost

        # 计算换手
        turnover_count = 0
        if i > 0:
            prev_holdings = set(holdings_history[i-1]['stocks'])
            curr_holdings = set(selected)
            turnover_count = len(prev_holdings.symmetric_difference(curr_holdings))
            total_turnover += turnover_count

        # 计算到下一期的收益
        if i < len(rebalance_dates) - 1:
            next_date = rebalance_dates[i + 1]
            capital_per_stock = current_value / len(selected)

            # Phase 6F: 止盈逻辑
            active_stocks = selected.copy()  # 当前周期持仓

            if take_profit_tiers and len(take_profit_tiers) > 0:
                # 先计算每只股票的收益率，检查是否触发止盈
                for symbol in selected:
                    df = stock_data[symbol]

                    if date not in df.index or next_date not in df.index:
                        continue

                    buy_price = df.loc[date, 'close']
                    sell_price = df.loc[next_date, 'close']
                    period_return = (sell_price - buy_price) / buy_price

                    # 检查是否触发止盈（从高到低检查梯度）
                    for tier_idx, tier_threshold in enumerate(sorted(take_profit_tiers, reverse=True)):
                        if period_return >= tier_threshold:
                            # 触发止盈，记录并从active_stocks移除
                            take_profit_triggers.append({
                                'symbol': symbol,
                                'date': next_date.strftime('%Y-%m-%d'),
                                'tier': tier_idx + 1,
                                'threshold': tier_threshold,
                                'return': period_return
                            })
                            active_stocks.remove(symbol)

                            if debug:
                                print(f"[止盈触发] {symbol} @ {next_date.date()}: 收益{period_return*100:.2f}% >= 梯度{tier_threshold*100:.0f}%")
                            break

            # 计算期末价值（仅计算仍持有的股票）
            period_value = 0
            if len(active_stocks) > 0:
                # 资金仅分配给仍持有的股票
                capital_per_active_stock = current_value / len(active_stocks)

                for symbol in active_stocks:
                    df = stock_data[symbol]

                    if date not in df.index or next_date not in df.index:
                        period_value += capital_per_active_stock
                        continue

                    buy_price = df.loc[date, 'close']
                    sell_price = df.loc[next_date, 'close']

                    shares = capital_per_active_stock / buy_price
                    period_value += shares * sell_price
            else:
                # 所有股票都触发止盈，资金保持现金
                period_value = current_value

            current_value = period_value

            # 扣除交易成本（买卖双边）
            if commission > 0 and turnover_count > 0:
                # 换手成本 = 换手股票数 * 每只股票金额 * 佣金率 * 2（买卖双边）
                trade_cost = turnover_count * capital_per_stock * commission * 2
                current_value -= trade_cost

    total_return = (current_value - initial_capital) / initial_capital
    turnover_rate = total_turnover / (len(rebalance_dates) * 10) * 100

    result = {
        'final_value': current_value,
        'total_return': total_return,
        'turnover': turnover_rate,
        'holdings_history': holdings_history
    }

    # Phase 6F: 添加止盈统计
    if take_profit_tiers:
        result['take_profit'] = {
            'enabled': True,
            'tiers': take_profit_tiers,
            'trigger_count': len(take_profit_triggers),
            'triggers': take_profit_triggers
        }
    else:
        result['take_profit'] = {
            'enabled': False
        }

    return result


def calculate_benchmark_return(benchmark_df, start_date, end_date):
    """
    计算沪深300指数收益

    Args:
        benchmark_df: 沪深300数据
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        float: 总收益率
    """
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    # 找到最接近的交易日
    benchmark_df = benchmark_df.set_index('date')
    available_dates = benchmark_df.index

    start_price = benchmark_df.loc[available_dates[available_dates >= start_ts][0], 'close']
    end_price = benchmark_df.loc[available_dates[available_dates <= end_ts][-1], 'close']

    return (end_price - start_price) / start_price


def run_backtest_with_config(config, benchmark_df, pool_stocks,
                             pool_name, target_count=None,
                             momentum_threshold=0.0, rebalance_freq='monthly',
                             commission=0.0, stability_ratio=0.0, take_profit_tiers=None, debug=False):
    """
    薄封装：解析config，委托给核心回测逻辑

    Args:
        config: 配置字典 {'start_date', 'end_date', 'rebalance_dates', 'target_count'}
        benchmark_df: 沪深300数据
        pool_stocks: 股票池数据（dict {symbol: name}）
        pool_name: 股票池名称
        target_count: 目标持仓数（可选，优先使用config中的值）
        其他参数同_run_year_backtest_core

    Returns:
        dict: 回测结果
    """
    start_date = config['start_date']
    end_date = config['end_date']
    rebalance_dates = config['rebalance_dates']

    # target_count优先使用config中的值
    if 'target_count' in config:
        target_count = config['target_count']
    elif target_count is None:
        # 如果都没有，推导
        target_count = derive_target_count(pool_name, pool_stocks, None)

    return _run_year_backtest_core(
        start_date, end_date, rebalance_dates,
        benchmark_df, pool_stocks, pool_name,
        target_count, momentum_threshold, commission,
        stability_ratio, take_profit_tiers, debug
    )


def run_year_backtest(year, benchmark_df, momentum_threshold=0.0, rebalance_freq='monthly', pool_name='small_cap', commission=0.0, stability_ratio=0.0, target_count=20, take_profit_tiers=None, debug=False):
    """
    执行指定年份的完整回测（薄包装，委托给run_backtest_with_config）

    Args:
        year: 年份（字符串）
        benchmark_df: 沪深300数据
        momentum_threshold: 20日涨幅阈值（百分比）
        rebalance_freq: 调仓频率（'monthly' 或 'quarterly'）
        pool_name: 股票池名称
        commission: 单边交易佣金率
        stability_ratio: 持仓稳定性比例
        target_count: 目标持仓数量
        take_profit_tiers: 止盈梯度列表
        debug: 是否启用DEBUG日志

    Returns:
        dict: 回测结果
    """
    config = get_year_config(year, rebalance_freq)
    if not config:
        raise ValueError(f"不支持的年份: {year}")

    # 加载股票池
    pool_stocks = load_stock_pool_from_yaml(pool_name)

    # 委托给薄封装
    return run_backtest_with_config(
        config, benchmark_df, pool_stocks, pool_name,
        target_count, momentum_threshold, rebalance_freq,
        commission, stability_ratio, take_profit_tiers, debug
    )


def _run_year_backtest_core(start_date, end_date, rebalance_dates,
                            benchmark_df, pool_stocks, pool_name,
                            target_count, momentum_threshold, commission,
                            stability_ratio, take_profit_tiers, debug):
    """
    核心回测逻辑（原run_year_backtest的主体，原地不动，只是重命名）

    Args:
        start_date: 起始日期
        end_date: 结束日期
        rebalance_dates: 调仓日期列表
        benchmark_df: 沪深300数据
        pool_stocks: 股票池 (dict {symbol: name})
        pool_name: 股票池名称
        target_count: 目标持仓数
        momentum_threshold: 动量阈值
        commission: 佣金率
        stability_ratio: 稳定性系数
        take_profit_tiers: 止盈梯度列表
        debug: 调试开关

    Returns:
        dict: 回测结果
    """
    # 以下是原run_year_backtest的核心逻辑（从593行开始）

    # 确定year标识（用于输出）
    year_label = f"{start_date[:4]}" if start_date else "Custom"

    print(f"\n{'='*60}")
    print(f"Phase 6D: {year_label}年回测 ({start_date} ~ {end_date})")
    print(f"  参数: 阈值={momentum_threshold}%, 佣金={commission*100:.2f}%, 稳定性={stability_ratio:.1f}")
    print(f"{'='*60}\n")

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data(data_dir, start_date, end_date, pool_name=pool_name)

    # 动态检查：至少需要5只股票（支持legacy_7stocks）
    if len(stock_data) < 5:
        raise ValueError(
            f"数据不足: 仅加载{len(stock_data)}只股票（最少需要5只）。"
            f"请确认已将 {start_date} ~ {end_date} 区间内的数据转换到 ~/.qlib/qlib_data/cn_data"
        )

    # 固定持仓回测
    print("\n执行固定持仓回测...")
    fixed_result = backtest_fixed(stock_data, commission=commission)
    print(f"✓ 固定持仓: 收益{fixed_result['total_return']*100:.2f}%")

    # 动态选股回测
    print("执行动态选股回测...")
    dynamic_result = backtest_dynamic(stock_data, rebalance_dates, momentum_threshold=momentum_threshold, commission=commission, stability_ratio=stability_ratio, target_count=target_count, take_profit_tiers=take_profit_tiers, debug=debug)
    print(f"✓ 动态选股: 收益{dynamic_result['total_return']*100:.2f}%")

    # 沪深300基准
    print("计算沪深300基准...")
    hs300_return = calculate_benchmark_return(
        benchmark_df, start_date, end_date
    )
    print(f"✓ 沪深300: 收益{hs300_return*100:.2f}%")

    # 计算年化收益
    months = len(rebalance_dates)
    years_period = months / 12

    annual_return_fixed = (1 + fixed_result['total_return']) ** (1 / years_period) - 1
    annual_return_dynamic = (1 + dynamic_result['total_return']) ** (1 / years_period) - 1
    annual_return_hs300 = (1 + hs300_return) ** (1 / years_period) - 1

    # 超额收益
    excess_vs_fixed = dynamic_result['total_return'] - fixed_result['total_return']
    excess_vs_hs300 = dynamic_result['total_return'] - hs300_return

    # 汇总结果（注意：Sharpe已移除）
    result = {
        'year': year_label,
        'months': months,
        'fixed': {
            'total_return': fixed_result['total_return'],
            'annual_return': annual_return_fixed,
            'final_value': fixed_result['final_value']
        },
        'dynamic': {
            'total_return': dynamic_result['total_return'],
            'annual_return': annual_return_dynamic,
            'final_value': dynamic_result['final_value'],
            'turnover': dynamic_result['turnover']
        },
        'hs300': {
            'total_return': hs300_return,
            'annual_return': annual_return_hs300
        },
        'excess': {
            'vs_fixed': excess_vs_fixed,
            'vs_hs300': excess_vs_hs300
        }
    }

    return result


def judge_backtest_results(results_2022, results_2023, results_2024):
    """
    三层优先级判断：失效 > 归因异常 > 通过
    （注意：已移除过拟合检测，因为需要Sharpe指标）

    Args:
        results_2022/2023/2024: 各年份回测结果

    Returns:
        dict: 判定结果（含完整metrics）
    """
    return_2022 = results_2022['dynamic']['total_return']
    return_2023 = results_2023['dynamic']['total_return']
    return_2024 = results_2024['dynamic']['total_return']

    excess_vs_hs300 = [
        results_2022['excess']['vs_hs300'],
        results_2023['excess']['vs_hs300'],
        results_2024['excess']['vs_hs300']
    ]

    # ===== 优先级1: 策略失效（2022年红线） =====
    if return_2022 < THRESHOLDS['return_min_2022']:
        result = {
            'status': 'FAILED',
            'trigger': '2022年熊市失效',
            'next_step': 'Phase 6D-2（空仓机制验证）',
            'reason': f"2022年收益={return_2022:.2%} < {THRESHOLDS['return_min_2022']:.0%}（红线）"
        }

    # ===== 优先级2: 市场归因异常 =====
    elif (excess_vs_hs300[1] - excess_vs_hs300[0] > THRESHOLDS['excess_acceleration']) and \
         (excess_vs_hs300[2] - excess_vs_hs300[1] > THRESHOLDS['excess_acceleration']):
        result = {
            'status': 'WARNING',
            'trigger': '超额收益逐年加速，可能牛市过拟合',
            'next_step': 'Phase 6D-1B（方案B细分）或Phase 6E（扩大样本）',
            'reason': f"vs沪深300超额: 2022={excess_vs_hs300[0]:.1%} → " + \
                     f"2023={excess_vs_hs300[1]:.1%} → 2024={excess_vs_hs300[2]:.1%}"
        }

    # ===== 全部通过 =====
    else:
        result = {
            'status': 'PASSED',
            'trigger': '三年稳健性验证通过',
            'next_step': 'Phase 6E（股票池扩展）',
            'reason': f"2022年收益>={THRESHOLDS['return_min_2022']:.0%}，三年表现稳定"
        }

    # ===== 附加完整metrics =====
    result['metrics'] = {
        '2022': {
            **results_2022['dynamic'],
            'hs300_return': results_2022['hs300']['total_return'],
            'excess_vs_fixed': results_2022['excess']['vs_fixed'],
            'excess_vs_hs300': results_2022['excess']['vs_hs300']
        },
        '2023': {
            **results_2023['dynamic'],
            'hs300_return': results_2023['hs300']['total_return'],
            'excess_vs_fixed': results_2023['excess']['vs_fixed'],
            'excess_vs_hs300': results_2023['excess']['vs_hs300']
        },
        '2024': {
            **results_2024['dynamic'],
            'hs300_return': results_2024['hs300']['total_return'],
            'excess_vs_fixed': results_2024['excess']['vs_fixed'],
            'excess_vs_hs300': results_2024['excess']['vs_hs300']
        }
    }

    result['config'] = {
        'thresholds': THRESHOLDS,
        'stock_pool_size': 10,
        'years_tested': [2022, 2023, 2024]
    }

    return result


def generate_comparison_report(results_2022, results_2023, results_2024, judgment):
    """
    生成对比报告（markdown格式）

    Args:
        results_2022/2023/2024: 各年份结果
        judgment: 判定结果

    Returns:
        str: markdown内容
    """
    md = f"""# Phase 6D: 三年稳健性验证报告

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 验收结果: **{judgment['status']}**

## 验收判断

- **状态**: {judgment['status']}
- **触发条件**: {judgment['trigger']}
- **下一步**: {judgment['next_step']}
- **原因**: {judgment['reason']}

---

## 动态选股策略表现

| 年份 | 总收益 | 年化收益 | 换手率 | 超额(vs固定) | 超额(vs300) |
|------|--------|---------|--------|-------------|------------|
"""

    for year_str, year_key in [('2022', '2022'), ('2023', '2023'), ('2024', '2024')]:
        m = judgment['metrics'][year_key]
        md += f"| {year_str} | {m['total_return']*100:>6.2f}% | {m['annual_return']*100:>7.2f}% | {m['turnover']:>6.2f}% | {m['excess_vs_fixed']*100:>+6.2f}% | {m['excess_vs_hs300']*100:>+6.2f}% |\n"

    md += """
---

## 固定持仓基准表现

| 年份 | 总收益 | 年化收益 |
|------|--------|---------|
"""

    for year_str, results in [('2022', results_2022), ('2023', results_2023), ('2024', results_2024)]:
        f = results['fixed']
        md += f"| {year_str} | {f['total_return']*100:>6.2f}% | {f['annual_return']*100:>7.2f}% |\n"

    md += """
---

## 沪深300基准表现

| 年份 | 总收益 | 年化收益 |
|------|--------|---------|
"""

    for year_str, results in [('2022', results_2022), ('2023', results_2023), ('2024', results_2024)]:
        h = results['hs300']
        md += f"| {year_str} | {h['total_return']*100:>6.2f}% | {h['annual_return']*100:>7.2f}% |\n"

    md += f"""
---

## 红线检查

### 2022年（熊市红线）
- 总收益率: {judgment['metrics']['2022']['total_return']*100:.2f}% {'✅' if judgment['metrics']['2022']['total_return'] > THRESHOLDS['return_min_2022'] else '❌'} （阈值: {THRESHOLDS['return_min_2022']*100:.0f}%）
- 超额收益(vs沪深300): {judgment['metrics']['2022']['excess_vs_hs300']*100:+.2f}%

### 2023年（结构性牛市）
- 总收益率: {judgment['metrics']['2023']['total_return']*100:.2f}%
- 超额收益(vs沪深300): {judgment['metrics']['2023']['excess_vs_hs300']*100:+.2f}%

### 2024年（震荡市）
- 总收益率: {judgment['metrics']['2024']['total_return']*100:.2f}%
- 超额收益(vs沪深300): {judgment['metrics']['2024']['excess_vs_hs300']*100:+.2f}%

---

## 关键发现

1. **市场归因**：
   - 2022年沪深300跌{results_2022['hs300']['total_return']*100:.2f}%，策略{'亏损' if judgment['metrics']['2022']['total_return'] < 0 else '盈利'}{abs(judgment['metrics']['2022']['total_return'])*100:.2f}%
   - 2023年沪深300涨{results_2023['hs300']['total_return']*100:.2f}%，策略盈利{judgment['metrics']['2023']['total_return']*100:.2f}%
   - 2024年沪深300涨{results_2024['hs300']['total_return']*100:.2f}%，策略盈利{judgment['metrics']['2024']['total_return']*100:.2f}%

2. **超额收益趋势**：
   - vs沪深300: 2022年{judgment['metrics']['2022']['excess_vs_hs300']*100:+.2f}% → 2023年{judgment['metrics']['2023']['excess_vs_hs300']*100:+.2f}% → 2024年{judgment['metrics']['2024']['excess_vs_hs300']*100:+.2f}%

3. **换手率分析**：
   - 2022年: {judgment['metrics']['2022']['turnover']:.2f}%
   - 2023年: {judgment['metrics']['2023']['turnover']:.2f}%
   - 2024年: {judgment['metrics']['2024']['turnover']:.2f}%

---

## 结论

{judgment['trigger']}

**推荐下一步**: {judgment['next_step']}

---

*报告生成: Phase 6D v1.0.0*
"""

    return md


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Phase 6D: 三年稳健性验证')
    parser.add_argument('--year', type=str, default='2024',
                        help='回测年份: 2022/2023/2024 (默认2024)')
    parser.add_argument('--full', action='store_true',
                        help='执行完整三年回测并生成判定报告')
    parser.add_argument('--momentum-threshold', type=float, default=0.0,
                        help='20日涨幅阈值（%%），默认0.0，建议-5.0~0.0')
    parser.add_argument('--rebalance-freq', type=str, default='monthly',
                        choices=['monthly', 'quarterly'],
                        help='调仓频率（默认monthly）')
    parser.add_argument('--pool', type=str, default='medium_cap',
                        choices=['small_cap', 'medium_cap', 'legacy_7stocks'],
                        help='股票池（默认medium_cap=20只[推荐], small_cap=10只[legacy], legacy_7stocks=7只[Phase 8]）')
    parser.add_argument('--commission', type=float, default=0.0,
                        help='单边交易佣金率（默认0.0，示例：0.001=0.1%%）')
    parser.add_argument('--stability-ratio', type=float, default=0.0,
                        help='持仓稳定性比例（0=关闭，0.5=优先保留50%%老仓位，范围0-1）')
    parser.add_argument('--debug', action='store_true',
                        help='启用DEBUG日志输出')
    parser.add_argument('--take-profit', type=str, default=None,
                        help='止盈梯度（逗号分隔，如"10,15"表示10%%和15%%），默认None关闭')
    parser.add_argument('--start-date', type=str,
                        help='Pilot模式：自定义起始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='Pilot模式：自定义结束日期 (YYYY-MM-DD)')
    parser.add_argument('--with-ai-probe', action='store_true',
                        help='Phase 9A: 回测后运行AI探针分析（需要设置 OPENAI_API_KEY）')
    args = parser.parse_args()
    
    # Legacy pool warning
    if args.pool == 'small_cap':
        print("\n" + "="*60)
        print("[WARNING] Using legacy small_cap (10-stock) pool.")
        print("          Production recommendation: medium_cap (20-stock).")
        print("          See PHASE6E_SUMMARY.md for details.")
        print("="*60 + "\n")
    
    # 初始化目录
    ensure_directories()

    # Phase 8.1: Pilot模式检查
    pilot_mode = args.year == 'pilot' or (args.start_date and args.end_date)

    if pilot_mode:
        # Pilot模式：自定义时间区间
        if not args.start_date or not args.end_date:
            print("❌ Pilot模式需要同时提供 --start-date 和 --end-date")
            sys.exit(1)

        benchmark_start = args.start_date
        print(f"\n🚀 Phase 8.1 Pilot模式: {args.start_date} ~ {args.end_date}")
    elif args.full:
        # 完整三年模式
        benchmark_start = '2022-01-01'
    else:
        # 单年模式
        single_year_config = get_year_config(args.year, args.rebalance_freq)
        if not single_year_config:
            print(f"❌ 不支持的年份: {args.year}")
            sys.exit(1)
        benchmark_start = single_year_config['start_date']

    # 加载沪深300基准
    benchmark_df = load_benchmark_data(start_date=benchmark_start)

    # Phase 6F: 解析止盈梯度参数
    take_profit_tiers = None
    if args.take_profit:
        take_profit_tiers = [float(x)/100 for x in args.take_profit.split(',')]
        print(f"✓ 启用固定止盈: {[f'{t*100:.0f}%' for t in take_profit_tiers]}")

    # 生成文件名后缀
    freq_suffix = 'quarterly' if args.rebalance_freq == 'quarterly' else 'monthly'
    threshold_str = f"m{int(args.momentum_threshold)}" if args.momentum_threshold != 0 else "m0"

    # 根据股票池确定目标持仓数量和文件后缀（Phase 8扩展）
    if args.pool == 'legacy_7stocks':
        target_count = 7
        pool_suffix = '7stocks'
    elif args.pool == 'medium_cap':
        target_count = 20
        pool_suffix = '20stocks'
    else:  # small_cap
        target_count = 10
        pool_suffix = '10stocks'

    file_suffix = f"_{threshold_str}_{freq_suffix}_{pool_suffix}"

    if pilot_mode:
        # Phase 8.1: Pilot模式执行
        print("\n" + "="*60)
        print(f"Phase 8.1 Pilot: {args.pool} 池回测")
        print(f"时间区间: {args.start_date} ~ {args.end_date}")
        print(f"参数: 阈值={args.momentum_threshold}%, 佣金={args.commission*100:.2f}%, 稳定性={args.stability_ratio:.1f}")
        print("="*60)

        # 加载股票池
        pool_stocks = load_stock_pool_from_yaml(args.pool)

        # 构建pilot配置
        pilot_config = build_custom_config(
            args.start_date, args.end_date,
            args.pool, pool_stocks,
            freq='M',  # 月末调仓
            target_count=target_count
        )

        # 执行回测
        result = run_backtest_with_config(
            pilot_config, benchmark_df, pool_stocks, args.pool,
            target_count, args.momentum_threshold, args.rebalance_freq,
            args.commission, args.stability_ratio, take_profit_tiers, args.debug
        )

        # 打印摘要
        print(f"\n{'-'*60}")
        print("Pilot回测摘要")
        print(f"{'-'*60}")
        print(f"时间区间: {args.start_date} ~ {args.end_date} ({result['months']}个月)")
        print(f"动态选股: {result['dynamic']['total_return']*100:.2f}% (年化{result['dynamic']['annual_return']*100:.2f}%, 换手{result['dynamic']['turnover']:.2f}%)")
        print(f"固定持仓: {result['fixed']['total_return']*100:.2f}% (年化{result['fixed']['annual_return']*100:.2f}%)")
        print(f"沪深300: {result['hs300']['total_return']*100:.2f}% (年化{result['hs300']['annual_return']*100:.2f}%)")
        print(f"超额收益(vs固定): {result['excess']['vs_fixed']*100:+.2f}%")
        print(f"超额收益(vs300): {result['excess']['vs_hs300']*100:+.2f}%")
        print()

        # 保存pilot结果
        pilot_suffix = f"_pilot_{args.pool}_{args.start_date[:4]}-{args.end_date[:4]}"
        save_json_with_metadata(
            data=result,
            filepath=f'results/phase8{pilot_suffix}.json',
            phase='Phase 8.1 Pilot',
            version='1.0.0'
        )
        print(f"✓ Pilot结果已保存: results/phase8{pilot_suffix}.json")

    elif args.full:
        # 完整三年回测
        print("\n" + "="*60)
        print("Phase 6D: 完整三年回测模式")
        print(f"参数: 阈值={args.momentum_threshold}%, 频率={args.rebalance_freq}, 佣金={args.commission*100:.2f}%, 稳定性={args.stability_ratio:.1f}")
        print("="*60)

        results_2022 = run_year_backtest('2022', benchmark_df, args.momentum_threshold, args.rebalance_freq, args.pool, args.commission, args.stability_ratio, target_count, take_profit_tiers, args.debug)
        results_2023 = run_year_backtest('2023', benchmark_df, args.momentum_threshold, args.rebalance_freq, args.pool, args.commission, args.stability_ratio, target_count, take_profit_tiers, args.debug)
        results_2024 = run_year_backtest('2024', benchmark_df, args.momentum_threshold, args.rebalance_freq, args.pool, args.commission, args.stability_ratio, target_count, take_profit_tiers, args.debug)

        # 判定结果
        print("\n" + "="*60)
        print("执行验收判定...")
        print("="*60)

        judgment = judge_backtest_results(results_2022, results_2023, results_2024)

        # 打印判定结果
        print(f"\n状态: {judgment['status']}")
        print(f"触发条件: {judgment['trigger']}")
        print(f"下一步: {judgment['next_step']}")
        print(f"原因: {judgment['reason']}")

        # 保存判定结果到JSON（带后缀）
        save_json_with_metadata(
            data=judgment,
            filepath=f'results/phase6d_judgment{file_suffix}.json',
            phase='Phase 6D',
            version='1.0.0'
        )

        # 生成对比报告（带后缀）
        report = generate_comparison_report(results_2022, results_2023, results_2024, judgment)
        report_path = f'results/phase6d_comparison{file_suffix}.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✓ 对比报告已保存: {report_path}")

    else:
        # 单年回测
        result = run_year_backtest(args.year, benchmark_df, args.momentum_threshold, args.rebalance_freq, args.pool, args.commission, args.stability_ratio, target_count, take_profit_tiers, args.debug)

        # 打印摘要
        print(f"\n{'-'*60}")
        print("回测摘要")
        print(f"{'-'*60}")
        print(f"动态选股: {result['dynamic']['total_return']*100:.2f}% (年化{result['dynamic']['annual_return']*100:.2f}%, 换手{result['dynamic']['turnover']:.2f}%)")
        print(f"固定持仓: {result['fixed']['total_return']*100:.2f}% (年化{result['fixed']['annual_return']*100:.2f}%)")
        print(f"沪深300: {result['hs300']['total_return']*100:.2f}% (年化{result['hs300']['annual_return']*100:.2f}%)")
        print(f"超额收益(vs固定): {result['excess']['vs_fixed']*100:+.2f}%")
        print(f"超额收益(vs300): {result['excess']['vs_hs300']*100:+.2f}%")
        print()

    # Phase 9A: AI探针集成
    if args.with_ai_probe:
        print("\n" + "="*60)
        print("Phase 9A: 启动 AI 探针分析")
        print("="*60)

        # 检查环境变量
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量")
            print("   请运行: export OPENAI_API_KEY=your_api_key")
            print("   跳过 AI 探针分析")
        else:
            try:
                # 调用 AI 探针脚本
                probe_script = Path(__file__).parent / 'trading_agents_probe.py'

                print(f"✓ 调用探针脚本: {probe_script}")
                subprocess.run([
                    sys.executable,
                    str(probe_script),
                    '--max-samples', '10'
                ], check=True)

                print("✓ AI 探针分析完成")
                print("  查看结果: results/phase9a_ai_probe.csv")
                print("  查看汇总: results/phase9a_ai_probe_summary.json")

            except subprocess.CalledProcessError as e:
                print(f"❌ AI 探针执行失败: {e}")
            except Exception as e:
                print(f"❌ AI 探针错误: {e}")


if __name__ == "__main__":
    main()
