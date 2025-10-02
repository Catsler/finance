#!/usr/bin/env python3
"""
策略优化与对比分析

功能:
    1. 参数网格搜索 - 测试多组MA组合
    2. 基准策略对比 - 买入持有、等权重
    3. 策略对比可视化

用法:
    python scripts/strategy_optimization.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from itertools import product

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def load_stock_data(data_dir: Path) -> dict:
    """加载所有股票数据"""
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
        df = pd.read_csv(csv_file, index_col='date', parse_dates=True)
        df['symbol'] = symbol
        df['name'] = name
        data[symbol] = df

    return data


def calculate_momentum_signals(df: pd.DataFrame, short_window=20, long_window=60) -> pd.DataFrame:
    """计算动量信号"""
    df = df.copy()

    # 计算移动平均线
    df['ma_short'] = df['close'].rolling(window=short_window).mean()
    df['ma_long'] = df['close'].rolling(window=long_window).mean()

    # 计算持仓信号
    df['position'] = 0
    df.loc[df['ma_short'] > df['ma_long'], 'position'] = 1
    df.loc[df['ma_short'] <= df['ma_long'], 'position'] = 0

    # 计算收益率
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['position'].shift(1) * df['returns']

    return df


def backtest_momentum(stock_data: dict, short_window=20, long_window=60, initial_capital=100000) -> tuple:
    """回测动量策略"""
    # 深拷贝数据
    data_copy = {k: v.copy() for k, v in stock_data.items()}

    # 计算每只股票的信号
    for symbol in data_copy:
        data_copy[symbol] = calculate_momentum_signals(data_copy[symbol], short_window, long_window)

    # 获取所有日期
    all_dates = sorted(set.union(*[set(df.index) for df in data_copy.values()]))
    all_dates = pd.DatetimeIndex(all_dates)

    # 组合收益
    portfolio_returns = pd.Series(0.0, index=all_dates)

    for date in all_dates:
        active_stocks = []
        for symbol, df in data_copy.items():
            if date in df.index:
                row = df.loc[date]
                if row['position'] == 1 and not pd.isna(row['strategy_returns']):
                    active_stocks.append(row['strategy_returns'])

        if active_stocks:
            portfolio_returns[date] = np.mean(active_stocks)

    # 计算累计收益
    portfolio_df = pd.DataFrame({
        'date': all_dates,
        'daily_returns': portfolio_returns.values
    })
    portfolio_df.set_index('date', inplace=True)
    portfolio_df['cumulative_returns'] = (1 + portfolio_df['daily_returns']).cumprod()
    portfolio_df['portfolio_value'] = initial_capital * portfolio_df['cumulative_returns']

    # 计算回撤
    portfolio_df['running_max'] = portfolio_df['portfolio_value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['running_max']) / portfolio_df['running_max']

    return portfolio_df, data_copy


def backtest_buy_and_hold(stock_data: dict, initial_capital=100000) -> pd.DataFrame:
    """回测买入持有策略 - 等权重买入所有股票并持有"""
    # 获取所有日期
    all_dates = sorted(set.union(*[set(df.index) for df in stock_data.values()]))
    all_dates = pd.DatetimeIndex(all_dates)

    # 组合收益 - 等权重
    portfolio_returns = pd.Series(0.0, index=all_dates)

    for date in all_dates:
        daily_returns = []
        for symbol, df in stock_data.items():
            if date in df.index:
                ret = df.loc[date, 'close'] / df.loc[df.index[0], 'close'] - 1 if date != df.index[0] else 0
                daily_returns.append((df.loc[date, 'close'] - df.loc[df.index[df.index < date][-1] if len(df.index[df.index < date]) > 0 else df.index[0], 'close']) / df.loc[df.index[df.index < date][-1] if len(df.index[df.index < date]) > 0 else df.index[0], 'close'] if date in df.index and len(df.index[df.index < date]) > 0 else 0)

        if daily_returns:
            portfolio_returns[date] = np.mean(daily_returns)

    # 更简单的实现：直接用收益率
    portfolio_returns = pd.Series(0.0, index=all_dates)

    for date in all_dates:
        daily_returns = []
        for symbol, df in stock_data.items():
            if date in df.index:
                df_sorted = df.sort_index()
                if date == df_sorted.index[0]:
                    daily_returns.append(0.0)
                else:
                    prev_dates = df_sorted.index[df_sorted.index < date]
                    if len(prev_dates) > 0:
                        prev_date = prev_dates[-1]
                        ret = (df_sorted.loc[date, 'close'] - df_sorted.loc[prev_date, 'close']) / df_sorted.loc[prev_date, 'close']
                        daily_returns.append(ret)

        if daily_returns:
            portfolio_returns[date] = np.mean(daily_returns)

    # 计算累计收益
    portfolio_df = pd.DataFrame({
        'date': all_dates,
        'daily_returns': portfolio_returns.values
    })
    portfolio_df.set_index('date', inplace=True)
    portfolio_df['cumulative_returns'] = (1 + portfolio_df['daily_returns']).cumprod()
    portfolio_df['portfolio_value'] = initial_capital * portfolio_df['cumulative_returns']

    # 计算回撤
    portfolio_df['running_max'] = portfolio_df['portfolio_value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['running_max']) / portfolio_df['running_max']

    return portfolio_df


def calculate_metrics(portfolio_df: pd.DataFrame, risk_free_rate=0.03) -> dict:
    """计算绩效指标"""
    total_return = portfolio_df['cumulative_returns'].iloc[-1] - 1
    trading_days = len(portfolio_df)
    years = trading_days / 252
    annual_return = (1 + total_return) ** (1 / years) - 1
    annual_volatility = portfolio_df['daily_returns'].std() * np.sqrt(252)
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
    max_drawdown = portfolio_df['drawdown'].min()
    win_rate = (portfolio_df['daily_returns'] > 0).sum() / len(portfolio_df)

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'final_value': portfolio_df['portfolio_value'].iloc[-1]
    }


def grid_search_parameters(stock_data: dict) -> pd.DataFrame:
    """网格搜索最优参数"""
    print("="*80)
    print("🔍 参数网格搜索")
    print("="*80)

    # 定义参数网格
    param_grid = [
        (5, 10),
        (5, 20),
        (10, 20),
        (10, 30),
        (20, 60),
        (30, 90),
        (50, 200)
    ]

    results = []

    for short, long in param_grid:
        print(f"\n测试参数: MA{short}/MA{long} ...", end=" ")

        try:
            portfolio_df, _ = backtest_momentum(stock_data, short, long)
            metrics = calculate_metrics(portfolio_df)

            results.append({
                'short_window': short,
                'long_window': long,
                'param_name': f'MA{short}/MA{long}',
                'total_return': metrics['total_return'],
                'annual_return': metrics['annual_return'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'max_drawdown': metrics['max_drawdown'],
                'final_value': metrics['final_value']
            })

            print(f"✅ Sharpe={metrics['sharpe_ratio']:.2f}, 年化收益={metrics['annual_return']*100:.2f}%")
        except Exception as e:
            print(f"❌ 失败: {e}")

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('sharpe_ratio', ascending=False)

    print("\n" + "="*80)
    print("📊 参数搜索结果 (按 Sharpe 排序)")
    print("="*80)
    print(results_df.to_string(index=False))

    return results_df


def compare_strategies(stock_data: dict) -> dict:
    """对比不同策略"""
    print("\n" + "="*80)
    print("📊 策略对比分析")
    print("="*80)

    strategies = {}

    # 1. 动量策略 MA20/MA60
    print("\n1️⃣ 动量策略 (MA20/MA60) ...", end=" ")
    momentum_df, _ = backtest_momentum(stock_data, 20, 60)
    strategies['动量策略 (MA20/MA60)'] = momentum_df
    print("✅")

    # 2. 买入持有
    print("2️⃣ 买入持有策略 ...", end=" ")
    bh_df = backtest_buy_and_hold(stock_data)
    strategies['买入持有'] = bh_df
    print("✅")

    # 3. 最优动量策略 (从网格搜索结果中选择)
    print("3️⃣ 优化动量策略 (MA10/MA30) ...", end=" ")
    optimized_df, _ = backtest_momentum(stock_data, 10, 30)
    strategies['优化动量策略 (MA10/MA30)'] = optimized_df
    print("✅")

    # 计算所有策略的指标
    comparison = []
    for name, df in strategies.items():
        metrics = calculate_metrics(df)
        comparison.append({
            '策略': name,
            '总收益率': f"{metrics['total_return']*100:.2f}%",
            '年化收益率': f"{metrics['annual_return']*100:.2f}%",
            'Sharpe比率': f"{metrics['sharpe_ratio']:.2f}",
            '最大回撤': f"{metrics['max_drawdown']*100:.2f}%",
            '最终价值': f"¥{metrics['final_value']:,.0f}"
        })

    comparison_df = pd.DataFrame(comparison)
    print("\n" + "="*80)
    print("策略绩效对比")
    print("="*80)
    print(comparison_df.to_string(index=False))

    return strategies


def plot_strategy_comparison(strategies: dict, output_path: Path):
    """绘制策略对比图"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

    # 1. 组合价值对比
    ax1 = axes[0]
    for i, (name, df) in enumerate(strategies.items()):
        ax1.plot(df.index, df['portfolio_value'], linewidth=2, label=name, color=colors[i % len(colors)])

    ax1.set_title('策略组合价值对比', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('组合价值 (元)')
    ax1.legend(loc='best')
    ax1.grid(alpha=0.3)
    ax1.axhline(y=100000, color='gray', linestyle='--', alpha=0.5, label='初始资金')

    # 2. 回撤对比
    ax2 = axes[1]
    for i, (name, df) in enumerate(strategies.items()):
        ax2.plot(df.index, df['drawdown'], linewidth=2, label=name, color=colors[i % len(colors)])

    ax2.set_title('策略回撤对比', fontsize=14, fontweight='bold')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('回撤 (%)')
    ax2.legend(loc='best')
    ax2.grid(alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}%'))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ 策略对比图已保存: {output_path}")


def main():
    """主函数"""
    print("="*80)
    print("Phase 3 - 策略优化与对比分析")
    print("="*80)

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data(data_dir)
    print(f"✅ 成功加载 {len(stock_data)} 只股票数据")

    # 1. 网格搜索
    results_df = grid_search_parameters(stock_data)

    # 保存参数搜索结果
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    results_df.to_csv(output_dir / "parameter_search_results.csv", index=False)
    print(f"\n✅ 参数搜索结果已保存: results/parameter_search_results.csv")

    # 2. 策略对比
    strategies = compare_strategies(stock_data)

    # 3. 绘制对比图
    plot_path = output_dir / "strategy_comparison.png"
    plot_strategy_comparison(strategies, plot_path)

    print("\n" + "="*80)
    print("✅ Phase 3 优化分析完成！")
    print("="*80)
    print(f"\n📁 输出文件:")
    print(f"   - 参数搜索结果: results/parameter_search_results.csv")
    print(f"   - 策略对比图: results/strategy_comparison.png")
    print("="*80)


if __name__ == "__main__":
    main()
