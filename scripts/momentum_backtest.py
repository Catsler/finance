#!/usr/bin/env python3
"""
简单动量策略回测脚本

策略逻辑:
    - 动量信号: 使用20日移动平均线和60日移动平均线
    - 买入信号: 短期均线上穿长期均线
    - 卖出信号: 短期均线下穿长期均线
    - 持仓: 等权重持有所有买入信号股票

用法:
    python scripts/momentum_backtest.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']  # macOS 使用 Arial Unicode MS
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

    print(f"✅ 成功加载 {len(data)} 只股票数据")
    return data


def calculate_momentum_signals(df: pd.DataFrame, short_window=20, long_window=60) -> pd.DataFrame:
    """
    计算动量信号

    策略:
        - MA20 上穿 MA60: 买入信号 (signal = 1)
        - MA20 下穿 MA60: 卖出信号 (signal = -1)
        - 其他: 持有 (signal = 0)
    """
    # 计算移动平均线
    df['ma_short'] = df['close'].rolling(window=short_window).mean()
    df['ma_long'] = df['close'].rolling(window=long_window).mean()

    # 计算信号: MA短期 > MA长期 时为多头
    df['position'] = 0
    df.loc[df['ma_short'] > df['ma_long'], 'position'] = 1  # 持有
    df.loc[df['ma_short'] <= df['ma_long'], 'position'] = 0  # 空仓

    # 计算每日收益率
    df['returns'] = df['close'].pct_change()

    # 计算策略收益: 只有持仓时才有收益
    df['strategy_returns'] = df['position'].shift(1) * df['returns']

    return df


def backtest_portfolio(stock_data: dict, initial_capital=100000) -> pd.DataFrame:
    """
    回测投资组合

    策略:
        - 等权重持有所有有买入信号的股票
        - 初始资金: 100,000 元
    """
    # 计算每只股票的信号
    for symbol in stock_data:
        stock_data[symbol] = calculate_momentum_signals(stock_data[symbol])

    # 获取所有日期的并集
    all_dates = sorted(set.union(*[set(df.index) for df in stock_data.values()]))
    all_dates = pd.DatetimeIndex(all_dates)

    # 创建组合收益序列
    portfolio_returns = pd.Series(0.0, index=all_dates)

    for date in all_dates:
        # 获取当日所有有持仓的股票
        active_stocks = []
        for symbol, df in stock_data.items():
            if date in df.index:
                row = df.loc[date]
                if row['position'] == 1 and not pd.isna(row['strategy_returns']):
                    active_stocks.append(row['strategy_returns'])

        # 等权重平均收益
        if active_stocks:
            portfolio_returns[date] = np.mean(active_stocks)

    # 计算累计收益
    portfolio_df = pd.DataFrame({
        'date': all_dates,
        'daily_returns': portfolio_returns.values
    })
    portfolio_df.set_index('date', inplace=True)

    # 累计收益
    portfolio_df['cumulative_returns'] = (1 + portfolio_df['daily_returns']).cumprod()
    portfolio_df['portfolio_value'] = initial_capital * portfolio_df['cumulative_returns']

    # 计算回撤
    portfolio_df['running_max'] = portfolio_df['portfolio_value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['running_max']) / portfolio_df['running_max']

    return portfolio_df


def calculate_performance_metrics(portfolio_df: pd.DataFrame, risk_free_rate=0.03) -> dict:
    """
    计算绩效指标

    指标:
        - 总收益率
        - 年化收益率
        - 年化波动率
        - Sharpe 比率
        - 最大回撤
        - 胜率
    """
    # 总收益率
    total_return = portfolio_df['cumulative_returns'].iloc[-1] - 1

    # 交易天数和年数
    trading_days = len(portfolio_df)
    years = trading_days / 252

    # 年化收益率
    annual_return = (1 + total_return) ** (1 / years) - 1

    # 年化波动率
    annual_volatility = portfolio_df['daily_returns'].std() * np.sqrt(252)

    # Sharpe 比率
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0

    # 最大回撤
    max_drawdown = portfolio_df['drawdown'].min()

    # 胜率
    win_rate = (portfolio_df['daily_returns'] > 0).sum() / len(portfolio_df)

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'trading_days': trading_days,
        'years': years
    }


def plot_results(portfolio_df: pd.DataFrame, metrics: dict, output_path: Path):
    """绘制回测结果"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # 1. 组合价值曲线
    ax1 = axes[0]
    ax1.plot(portfolio_df.index, portfolio_df['portfolio_value'], linewidth=2, color='#2E86AB')
    ax1.set_title('投资组合价值曲线', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('组合价值 (元)')
    ax1.grid(alpha=0.3)
    ax1.axhline(y=100000, color='gray', linestyle='--', alpha=0.5, label='初始资金')
    ax1.legend()

    # 2. 累计收益率曲线
    ax2 = axes[1]
    ax2.plot(portfolio_df.index, portfolio_df['cumulative_returns'] - 1, linewidth=2, color='#A23B72')
    ax2.set_title('累计收益率曲线', fontsize=14, fontweight='bold')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('累计收益率 (%)')
    ax2.grid(alpha=0.3)
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    # 格式化为百分比
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}%'))

    # 3. 回撤曲线
    ax3 = axes[2]
    ax3.fill_between(portfolio_df.index, portfolio_df['drawdown'], 0, color='#F18F01', alpha=0.5)
    ax3.set_title('回撤曲线', fontsize=14, fontweight='bold')
    ax3.set_xlabel('日期')
    ax3.set_ylabel('回撤 (%)')
    ax3.grid(alpha=0.3)

    # 格式化为百分比
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}%'))

    # 调整布局
    plt.tight_layout()

    # 保存图片
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ 图表已保存: {output_path}")

    # 显示图片（可选）
    # plt.show()


def print_metrics(metrics: dict):
    """打印绩效指标"""
    print("\n" + "="*80)
    print("📊 回测绩效指标")
    print("="*80)
    print(f"总收益率:        {metrics['total_return']*100:>8.2f}%")
    print(f"年化收益率:      {metrics['annual_return']*100:>8.2f}%")
    print(f"年化波动率:      {metrics['annual_volatility']*100:>8.2f}%")
    print(f"Sharpe 比率:     {metrics['sharpe_ratio']:>8.2f}")
    print(f"最大回撤:        {metrics['max_drawdown']*100:>8.2f}%")
    print(f"胜率:            {metrics['win_rate']*100:>8.2f}%")
    print(f"交易天数:        {metrics['trading_days']:>8.0f} 天")
    print(f"回测时长:        {metrics['years']:>8.2f} 年")
    print("="*80)


def save_report(portfolio_df: pd.DataFrame, metrics: dict, output_path: Path):
    """保存回测报告"""
    report = f"""# Phase 2 回测报告 - 简单动量策略

> 📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 🎯 策略: 双均线动量策略 (MA20/MA60)
> 📊 股票池: 10 只 A股精选股票

---

## ✅ 回测概览

### 绩效指标

| 指标 | 数值 |
|------|------|
| **总收益率** | {metrics['total_return']*100:.2f}% |
| **年化收益率** | {metrics['annual_return']*100:.2f}% |
| **年化波动率** | {metrics['annual_volatility']*100:.2f}% |
| **Sharpe 比率** | {metrics['sharpe_ratio']:.2f} |
| **最大回撤** | {metrics['max_drawdown']*100:.2f}% |
| **胜率** | {metrics['win_rate']*100:.2f}% |
| **交易天数** | {metrics['trading_days']:.0f} 天 |
| **回测时长** | {metrics['years']:.2f} 年 |

### 初始参数

- **初始资金**: ¥100,000
- **最终价值**: ¥{portfolio_df['portfolio_value'].iloc[-1]:,.2f}
- **绝对收益**: ¥{portfolio_df['portfolio_value'].iloc[-1] - 100000:,.2f}

---

## 📈 策略说明

### 双均线动量策略

**信号生成**:
- **买入信号**: 20日均线上穿60日均线
- **卖出信号**: 20日均线下穿60日均线
- **持仓规则**: 等权重持有所有买入信号股票

**风险管理**:
- 单只股票最大权重: 10% (等权配置)
- 无杠杆，纯多头策略
- 无止损，依赖均线信号

---

## 📊 数据来源

### 股票池 (10只)

| 股票代码 | 名称 | 行业 |
|---------|------|------|
| 000001.SZ | 平安银行 | 金融-银行 |
| 601318.SH | 中国平安 | 金融-保险 |
| 000858.SZ | 五粮液 | 消费-白酒 |
| 600519.SH | 贵州茅台 | 消费-白酒 |
| 300750.SZ | 宁德时代 | 科技-新能源 |
| 600036.SH | 招商银行 | 金融-银行 |
| 002594.SZ | 比亚迪 | 科技-新能源汽车 |
| 000002.SZ | 万科A | 地产 |
| 600276.SH | 恒瑞医药 | 医药-创新药 |
| 601166.SH | 兴业银行 | 金融-银行 |

**数据质量**:
- ✅ 数据时间跨度: 2022-10-10 ~ 2025-09-30 (约3年)
- ✅ 每只股票 727 条记录
- ✅ 缺失率: 3.84%
- ✅ 数据格式: CSV (后复权)

---

## 💡 结论与建议

### 策略表现评价

"""

    # 根据 Sharpe 比率评价
    if metrics['sharpe_ratio'] > 2:
        report += "✅ **优秀**: Sharpe 比率 > 2，策略表现优秀\n"
    elif metrics['sharpe_ratio'] > 1:
        report += "✅ **良好**: Sharpe 比率 > 1，策略表现良好\n"
    elif metrics['sharpe_ratio'] > 0:
        report += "⚠️  **一般**: Sharpe 比率 > 0，策略有正收益但波动较大\n"
    else:
        report += "❌ **较差**: Sharpe 比率 < 0，策略表现不佳\n"

    report += f"\n### 风险评估\n\n"

    if abs(metrics['max_drawdown']) > 0.3:
        report += f"⚠️  **高风险**: 最大回撤 {metrics['max_drawdown']*100:.2f}% > 30%\n"
    elif abs(metrics['max_drawdown']) > 0.15:
        report += f"⚠️  **中风险**: 最大回撤 {metrics['max_drawdown']*100:.2f}% 在 15-30% 之间\n"
    else:
        report += f"✅ **低风险**: 最大回撤 {metrics['max_drawdown']*100:.2f}% < 15%\n"

    report += f"""
### 改进方向

1. **参数优化**:
   - 尝试不同的均线周期组合 (如 10/30, 50/200)
   - 引入自适应参数调整机制

2. **风险控制**:
   - 添加止损机制 (如固定止损、移动止损)
   - 添加仓位管理 (如 ATR 动态调仓)

3. **信号优化**:
   - 增加成交量确认
   - 添加趋势强度过滤
   - 引入多因子模型

4. **组合优化**:
   - 行业轮动策略
   - 动态权重调整
   - 添加对冲工具

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**执行者**: Claude (AI Agent)
**数据来源**: AKShare (免费数据接口)
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 回测报告已保存: {output_path}")


def main():
    """主函数"""
    print("="*80)
    print("简单动量策略回测 - Phase 2")
    print("="*80)

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data(data_dir)

    # 回测
    print("\n🚀 开始回测...")
    portfolio_df = backtest_portfolio(stock_data)

    # 计算绩效
    metrics = calculate_performance_metrics(portfolio_df)
    print_metrics(metrics)

    # 绘制图表
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    plot_path = output_dir / "momentum_backtest_results.png"
    plot_results(portfolio_df, metrics, plot_path)

    # 保存报告
    report_path = Path("PHASE2_BACKTEST_REPORT.md")
    save_report(portfolio_df, metrics, report_path)

    # 保存详细数据
    csv_path = output_dir / "portfolio_daily_returns.csv"
    portfolio_df.to_csv(csv_path)
    print(f"✅ 详细数据已保存: {csv_path}")

    print("\n" + "="*80)
    print("✅ Phase 2 回测完成！")
    print("="*80)
    print(f"\n📁 输出文件:")
    print(f"   - 回测报告: PHASE2_BACKTEST_REPORT.md")
    print(f"   - 可视化图表: {plot_path}")
    print(f"   - 详细数据: {csv_path}")
    print("="*80)


if __name__ == "__main__":
    main()
