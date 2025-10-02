#!/usr/bin/env python3
"""
交易成本与风控优化回测

功能:
    1. 添加真实交易成本 (手续费 + 印花税)
    2. 实现固定止损 (-5%)
    3. 实现移动止损 (-10% 从最高点)
    4. 对比有无成本/止损的策略表现

用法:
    python scripts/risk_control_backtest.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

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


class TradingCostModel:
    """交易成本模型"""

    def __init__(self, commission_rate=0.0003, stamp_duty=0.001, min_commission=5):
        """
        Args:
            commission_rate: 佣金费率 (默认 0.03%)
            stamp_duty: 印花税 (默认 0.1%, 仅卖出收取)
            min_commission: 最低佣金 (默认 5 元)
        """
        self.commission_rate = commission_rate
        self.stamp_duty = stamp_duty
        self.min_commission = min_commission

    def calculate_cost(self, trade_amount: float, is_buy: bool) -> float:
        """
        计算交易成本

        Args:
            trade_amount: 交易金额
            is_buy: 是否买入 (True=买入, False=卖出)

        Returns:
            交易成本金额
        """
        # 佣金
        commission = max(trade_amount * self.commission_rate, self.min_commission)

        # 印花税 (仅卖出)
        stamp = trade_amount * self.stamp_duty if not is_buy else 0

        return commission + stamp


def backtest_with_cost_and_stop(
    stock_data: dict,
    short_window: int = 5,
    long_window: int = 10,
    enable_cost: bool = True,
    enable_fixed_stop: bool = False,
    enable_trailing_stop: bool = False,
    fixed_stop_loss: float = -0.05,
    trailing_stop_loss: float = -0.10,
    initial_capital: float = 100000
) -> pd.DataFrame:
    """
    带交易成本和止损的回测

    Args:
        stock_data: 股票数据字典
        short_window: 短期均线窗口
        long_window: 长期均线窗口
        enable_cost: 是否启用交易成本
        enable_fixed_stop: 是否启用固定止损
        enable_trailing_stop: 是否启用移动止损
        fixed_stop_loss: 固定止损比例 (如 -0.05 = -5%)
        trailing_stop_loss: 移动止损比例 (如 -0.10 = -10%)
        initial_capital: 初始资金

    Returns:
        回测结果 DataFrame
    """
    cost_model = TradingCostModel()

    # 深拷贝数据
    data_copy = {k: v.copy() for k, v in stock_data.items()}

    # 计算每只股票的信号
    for symbol in data_copy:
        df = data_copy[symbol]

        # 计算移动平均线
        df['ma_short'] = df['close'].rolling(window=short_window).mean()
        df['ma_long'] = df['close'].rolling(window=long_window).mean()

        # 基础信号
        df['signal'] = 0
        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
        df.loc[df['ma_short'] <= df['ma_long'], 'signal'] = 0

        # 初始化持仓和成本价
        df['position'] = 0
        df['entry_price'] = np.nan
        df['highest_price'] = np.nan

        # 逐日计算持仓和止损
        for i in range(1, len(df)):
            prev_position = df.iloc[i-1]['position']
            current_signal = df.iloc[i]['signal']
            current_price = df.iloc[i]['close']

            # 默认延续前一持仓
            df.iloc[i, df.columns.get_loc('position')] = prev_position

            # 如果有持仓，更新最高价
            if prev_position == 1:
                prev_entry = df.iloc[i-1]['entry_price']
                prev_highest = df.iloc[i-1]['highest_price']

                # 更新最高价
                new_highest = max(prev_highest, current_price)
                df.iloc[i, df.columns.get_loc('highest_price')] = new_highest
                df.iloc[i, df.columns.get_loc('entry_price')] = prev_entry

                # 检查固定止损
                if enable_fixed_stop:
                    return_rate = (current_price - prev_entry) / prev_entry
                    if return_rate <= fixed_stop_loss:
                        df.iloc[i, df.columns.get_loc('position')] = 0
                        df.iloc[i, df.columns.get_loc('entry_price')] = np.nan
                        df.iloc[i, df.columns.get_loc('highest_price')] = np.nan
                        continue

                # 检查移动止损
                if enable_trailing_stop:
                    drawdown = (current_price - new_highest) / new_highest
                    if drawdown <= trailing_stop_loss:
                        df.iloc[i, df.columns.get_loc('position')] = 0
                        df.iloc[i, df.columns.get_loc('entry_price')] = np.nan
                        df.iloc[i, df.columns.get_loc('highest_price')] = np.nan
                        continue

                # 检查卖出信号
                if current_signal == 0:
                    df.iloc[i, df.columns.get_loc('position')] = 0
                    df.iloc[i, df.columns.get_loc('entry_price')] = np.nan
                    df.iloc[i, df.columns.get_loc('highest_price')] = np.nan

            # 如果无持仓，检查买入信号
            elif prev_position == 0 and current_signal == 1:
                df.iloc[i, df.columns.get_loc('position')] = 1
                df.iloc[i, df.columns.get_loc('entry_price')] = current_price
                df.iloc[i, df.columns.get_loc('highest_price')] = current_price

        # 计算收益率
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['position'].shift(1) * df['returns']

        # 计算交易次数
        df['position_change'] = df['position'].diff()
        df['trades'] = ((df['position_change'] != 0) & (df['position_change'].notna())).astype(int)

    # 组合层面回测
    all_dates = sorted(set.union(*[set(df.index) for df in data_copy.values()]))
    all_dates = pd.DatetimeIndex(all_dates)

    # 初始化组合数据
    portfolio_value = initial_capital
    portfolio_values = []
    daily_returns = []
    total_trades = 0
    total_cost = 0

    for date in all_dates:
        # 收集当日所有持仓股票的收益
        active_returns = []
        day_trades = 0

        for symbol, df in data_copy.items():
            if date in df.index:
                row = df.loc[date]

                # 统计交易次数
                if row['trades'] == 1:
                    day_trades += 1

                # 收集收益
                if row['position'] == 1 and not pd.isna(row['strategy_returns']):
                    active_returns.append(row['strategy_returns'])

        # 计算当日收益
        if active_returns:
            avg_return = np.mean(active_returns)

            # 计算交易成本
            if enable_cost and day_trades > 0:
                # 简化处理：每笔交易按等权重计算成本
                trade_amount = portfolio_value / 10  # 假设等权分配
                cost_per_trade = cost_model.calculate_cost(trade_amount, is_buy=True)
                day_cost = cost_per_trade * day_trades
                total_cost += day_cost

                # 从收益中扣除成本
                cost_rate = day_cost / portfolio_value
                avg_return -= cost_rate

            total_trades += day_trades
        else:
            avg_return = 0

        # 更新组合价值
        portfolio_value *= (1 + avg_return)
        portfolio_values.append(portfolio_value)
        daily_returns.append(avg_return)

    # 创建结果 DataFrame
    portfolio_df = pd.DataFrame({
        'date': all_dates,
        'portfolio_value': portfolio_values,
        'daily_returns': daily_returns
    })
    portfolio_df.set_index('date', inplace=True)

    # 计算累计收益
    portfolio_df['cumulative_returns'] = portfolio_df['portfolio_value'] / initial_capital

    # 计算回撤
    portfolio_df['running_max'] = portfolio_df['portfolio_value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['running_max']) / portfolio_df['running_max']

    # 记录交易统计
    portfolio_df.attrs['total_trades'] = total_trades
    portfolio_df.attrs['total_cost'] = total_cost

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
        'final_value': portfolio_df['portfolio_value'].iloc[-1],
        'total_trades': portfolio_df.attrs.get('total_trades', 0),
        'total_cost': portfolio_df.attrs.get('total_cost', 0)
    }


def compare_scenarios(stock_data: dict) -> dict:
    """对比不同场景"""
    print("="*80)
    print("🔍 交易成本与风控影响分析")
    print("="*80)

    scenarios = {}

    # 场景1: 无成本无止损 (理想情况)
    print("\n1️⃣ 理想策略 (MA5/MA10, 无成本, 无止损) ...", end=" ")
    df1 = backtest_with_cost_and_stop(
        stock_data, 5, 10,
        enable_cost=False,
        enable_fixed_stop=False,
        enable_trailing_stop=False
    )
    scenarios['理想策略'] = df1
    print("✅")

    # 场景2: 有成本无止损 (真实情况)
    print("2️⃣ 真实策略 (MA5/MA10, 有成本, 无止损) ...", end=" ")
    df2 = backtest_with_cost_and_stop(
        stock_data, 5, 10,
        enable_cost=True,
        enable_fixed_stop=False,
        enable_trailing_stop=False
    )
    scenarios['真实策略'] = df2
    print("✅")

    # 场景3: 有成本 + 固定止损
    print("3️⃣ 固定止损策略 (MA5/MA10, 有成本, -5%止损) ...", end=" ")
    df3 = backtest_with_cost_and_stop(
        stock_data, 5, 10,
        enable_cost=True,
        enable_fixed_stop=True,
        enable_trailing_stop=False,
        fixed_stop_loss=-0.05
    )
    scenarios['固定止损策略'] = df3
    print("✅")

    # 场景4: 有成本 + 移动止损
    print("4️⃣ 移动止损策略 (MA5/MA10, 有成本, -10%移动止损) ...", end=" ")
    df4 = backtest_with_cost_and_stop(
        stock_data, 5, 10,
        enable_cost=True,
        enable_fixed_stop=False,
        enable_trailing_stop=True,
        trailing_stop_loss=-0.10
    )
    scenarios['移动止损策略'] = df4
    print("✅")

    # 场景5: 有成本 + 双重止损
    print("5️⃣ 双重止损策略 (MA5/MA10, 有成本, -5%固定 + -10%移动) ...", end=" ")
    df5 = backtest_with_cost_and_stop(
        stock_data, 5, 10,
        enable_cost=True,
        enable_fixed_stop=True,
        enable_trailing_stop=True,
        fixed_stop_loss=-0.05,
        trailing_stop_loss=-0.10
    )
    scenarios['双重止损策略'] = df5
    print("✅")

    # 对比表格
    comparison = []
    for name, df in scenarios.items():
        metrics = calculate_metrics(df)
        comparison.append({
            '场景': name,
            '最终价值': f"¥{metrics['final_value']:,.0f}",
            '总收益率': f"{metrics['total_return']*100:.2f}%",
            '年化收益': f"{metrics['annual_return']*100:.2f}%",
            'Sharpe': f"{metrics['sharpe_ratio']:.2f}",
            '最大回撤': f"{metrics['max_drawdown']*100:.2f}%",
            '交易次数': f"{metrics['total_trades']:.0f}",
            '交易成本': f"¥{metrics['total_cost']:,.0f}"
        })

    comparison_df = pd.DataFrame(comparison)
    print("\n" + "="*80)
    print("📊 场景对比分析")
    print("="*80)
    print(comparison_df.to_string(index=False))

    return scenarios


def plot_scenario_comparison(scenarios: dict, output_path: Path):
    """绘制场景对比图"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']

    # 1. 组合价值对比
    ax1 = axes[0]
    for i, (name, df) in enumerate(scenarios.items()):
        ax1.plot(df.index, df['portfolio_value'], linewidth=2, label=name, color=colors[i % len(colors)])

    ax1.set_title('不同场景下的组合价值对比', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('组合价值 (元)')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(alpha=0.3)
    ax1.axhline(y=100000, color='gray', linestyle='--', alpha=0.5)

    # 2. 回撤对比
    ax2 = axes[1]
    for i, (name, df) in enumerate(scenarios.items()):
        ax2.plot(df.index, df['drawdown'], linewidth=2, label=name, color=colors[i % len(colors)])

    ax2.set_title('不同场景下的回撤对比', fontsize=14, fontweight='bold')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('回撤 (%)')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}%'))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ 场景对比图已保存: {output_path}")


def main():
    """主函数"""
    print("="*80)
    print("Phase 4 - 交易成本与风控优化")
    print("="*80)

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data(data_dir)
    print(f"✅ 成功加载 {len(stock_data)} 只股票数据")

    # 场景对比
    scenarios = compare_scenarios(stock_data)

    # 保存详细数据
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    for name, df in scenarios.items():
        csv_path = output_dir / f"scenario_{name.replace(' ', '_')}.csv"
        df.to_csv(csv_path)

    print(f"\n✅ 详细数据已保存至 results/ 目录")

    # 绘制对比图
    plot_path = output_dir / "risk_control_comparison.png"
    plot_scenario_comparison(scenarios, plot_path)

    print("\n" + "="*80)
    print("✅ Phase 4 风控优化完成！")
    print("="*80)
    print(f"\n📁 输出文件:")
    print(f"   - 场景对比图: results/risk_control_comparison.png")
    print(f"   - 详细数据: results/scenario_*.csv")
    print("="*80)


if __name__ == "__main__":
    main()
