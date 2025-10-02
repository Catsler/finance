#!/usr/bin/env python3
"""
Phase 6D补充：2023年复盘分析

⚠️ 注意：
- 该脚本使用 small_cap（10只股票池）
- 目的是诊断10只池在2023年的失效原因
- Phase 6E已证明：扩展到20只池后2023年问题修复（-18.16% → +6.10%）

功能:
    - 重新运行2023年逐月选股，记录持仓变化
    - 分析空仓月份、换手率、个股贡献
    - 输出CSV+TXT总结

注意:
    - 选股逻辑从 phase6d_backtest.py 复制
    - TODO: 将来如需修改筛选条件，需同步修改两处，或重构为 utils/stock_selection.py

用法:
    python scripts/phase6d_review_2023.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# 导入工具模块
sys.path.append(str(Path(__file__).parent.parent))


# ===== 股票池定义 =====
STOCK_POOL = {
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


# ===== 2023年调仓日期 =====
REBALANCE_DATES = [
    '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-28',
    '2023-05-31', '2023-06-30', '2023-07-31', '2023-08-31',
    '2023-09-28', '2023-10-31', '2023-11-30', '2023-12-29'
]


# ===== TODO: 以下代码复制自 phase6d_backtest.py，将来需同步修改 =====

def load_stock_data(data_dir, start_date, end_date):
    """
    加载股票数据

    Args:
        data_dir: 数据目录
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        dict: {symbol: DataFrame}
    """
    data = {}
    for symbol, name in STOCK_POOL.items():
        csv_file = Path(data_dir) / f'{symbol}.csv'
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


def select_stocks(stock_data, date):
    """
    选股规则：20日涨幅>0% AND MA5>MA10

    Returns:
        list of dict: [{'symbol': 'xxx', 'name': 'xxx', 'momentum_20d': x, 'ma5': x, 'ma10': x}]
    """
    selected = []

    for symbol, df in stock_data.items():
        ret_20d = calculate_20d_return(df, date)
        if pd.isna(ret_20d) or ret_20d <= 0:
            continue

        if not check_ma_crossover(df, date):
            continue

        selected.append({
            'symbol': symbol,
            'name': df.loc[date, 'name'],
            'momentum_20d': ret_20d,
            'ma5': df.loc[date, 'ma5'],
            'ma10': df.loc[date, 'ma10']
        })

    return selected


def calculate_period_return(stock_data, symbol, start_date, end_date):
    """
    计算某只股票在指定期间的收益率

    Returns:
        float: 收益率（如果数据缺失返回0.0）
    """
    try:
        df = stock_data[symbol]

        if start_date not in df.index or end_date not in df.index:
            return 0.0

        start_price = df.loc[start_date, 'close']
        end_price = df.loc[end_date, 'close']

        return (end_price - start_price) / start_price
    except:
        return 0.0


# ===== 复盘主逻辑 =====

def analyze_2023():
    """
    2023年逐月复盘分析

    Returns:
        DataFrame: 复盘结果
    """
    print("\n" + "="*60)
    print("Phase 6D: 2023年复盘分析")
    print("="*60 + "\n")

    # 加载数据
    data_dir = Path.home() / '.qlib/qlib_data/cn_data'
    stock_data = load_stock_data(data_dir, '2022-12-01', '2023-12-31')

    if len(stock_data) < 10:
        raise ValueError(f"数据不足: 仅加载{len(stock_data)}只股票")

    results = []
    prev_holdings = []

    # 逐月分析
    for i, date_str in enumerate(REBALANCE_DATES):
        date = pd.Timestamp(date_str)
        month_str = date.strftime('%Y-%m')

        print(f"\n分析 {month_str}...")

        # 选股
        selected = select_stocks(stock_data, date)
        current_symbols = [s['symbol'] for s in selected]

        # 计算换手率
        if i > 0:
            prev_set = set(prev_holdings)
            curr_set = set(current_symbols)
            turnover_count = len(prev_set.symmetric_difference(curr_set))
            turnover_rate = turnover_count / max(len(prev_set), 1) if prev_set else 0.0
        else:
            turnover_rate = 0.0

        # 分析空仓原因
        empty_reason = ""
        if len(selected) == 0:
            # 统计哪些股票通过了哪些条件
            passed_momentum = 0
            passed_ma = 0
            for symbol, df in stock_data.items():
                ret_20d = calculate_20d_return(df, date)
                if not pd.isna(ret_20d) and ret_20d > 0:
                    passed_momentum += 1
                if check_ma_crossover(df, date):
                    passed_ma += 1

            empty_reason = f"20日>0%:{passed_momentum}只, MA5>MA10:{passed_ma}只, 同时满足:0只"

        # 计算本月表现最好和最差的股票
        best_stock = ""
        worst_stock = ""
        best_return = -float('inf')
        worst_return = float('inf')

        if len(selected) > 0 and i < len(REBALANCE_DATES) - 1:
            next_date = pd.Timestamp(REBALANCE_DATES[i + 1])

            for stock in selected:
                ret = calculate_period_return(stock_data, stock['symbol'], date, next_date)
                if ret > best_return:
                    best_return = ret
                    best_stock = f"{stock['symbol']} ({ret*100:+.2f}%)"
                if ret < worst_return:
                    worst_return = ret
                    worst_stock = f"{stock['symbol']} ({ret*100:+.2f}%)"

        # 记录结果
        results.append({
            'month': month_str,
            'held_count': len(selected),
            'symbols': ';'.join(current_symbols),
            'turnover_rate': f'{turnover_rate:.1%}',
            'empty_reason': empty_reason,
            'best_stock': best_stock,
            'worst_stock': worst_stock
        })

        print(f"  持仓: {len(selected)}只")
        print(f"  换手: {turnover_rate:.1%}")
        if empty_reason:
            print(f"  空仓原因: {empty_reason}")

        prev_holdings = current_symbols

    return pd.DataFrame(results)


def generate_summary(df):
    """
    生成总结报告

    Args:
        df: 复盘数据

    Returns:
        str: 总结文本
    """
    empty_months = df[df['held_count'] == 0]
    avg_held = df['held_count'].mean()

    # 计算平均换手率（需要转换百分比字符串）
    turnover_values = df['turnover_rate'].str.rstrip('%').astype(float) / 100
    avg_turnover = turnover_values.mean()

    summary = f"""2023年复盘关键发现
==================
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. 空仓月份：{len(empty_months)}个月
   {', '.join(empty_months['month'].tolist()) if len(empty_months) > 0 else '无空仓月份'}

2. 平均换手率：{avg_turnover:.1%}
   (2022年7.5%, 2024年33.3%)

3. 平均持仓数：{avg_held:.1f}只 / 10只

4. 换手分布：
   - 0-10%: {len(df[turnover_values <= 0.1])}个月
   - 10-30%: {len(df[(turnover_values > 0.1) & (turnover_values <= 0.3)])}个月
   - 30-50%: {len(df[(turnover_values > 0.3) & (turnover_values <= 0.5)])}个月
   - 50%+: {len(df[turnover_values > 0.5])}个月

5. 主要问题待分析：
   - 如果空仓月份≥3：筛选条件过严（20日>0%与MA5>MA10不同步）
   - 如果平均换手>50%：过度交易
   - 需对比固定持仓中各股票的2023年收益，判断是否错失黑马

详细数据见: results/phase6d_2023_review.csv
"""

    return summary


def main():
    """主函数"""
    # 执行复盘
    df = analyze_2023()

    # 保存CSV
    output_csv = 'results/phase6d_2023_review.csv'
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n✓ 已保存: {output_csv}")

    # 生成总结
    summary = generate_summary(df)
    output_txt = 'results/phase6d_2023_summary.txt'
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"✓ 已保存: {output_txt}")

    # 打印总结
    print("\n" + "="*60)
    print(summary)
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
