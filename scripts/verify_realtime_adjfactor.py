#!/usr/bin/env python3
"""
实时行情与复权数据对齐验证脚本

功能：
1. 获取实时行情（真实价格）
2. 下载前复权实时数据
3. 读取本地前复权数据
4. 验证对齐情况

作者: Claude Code
日期: 2025-10-23
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.realtime_quote import get_realtime_quotes
import akshare as ak

def get_local_data(symbol: str, data_dir: Path) -> pd.DataFrame:
    """读取本地Qlib数据"""
    csv_file = data_dir / f"{symbol}.csv"

    if not csv_file.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_file, parse_dates=['date'])
    df = df.set_index('date')
    return df


def get_akshare_qfq_data(symbol: str, days: int = 10) -> pd.DataFrame:
    """
    从AKShare获取最近N天的前复权数据

    用于与实时行情对比验证
    """
    # 转换股票代码格式 (SH/SZ)
    if '.SH' in symbol:
        ak_symbol = symbol.replace('.SH', '')
    elif '.SZ' in symbol:
        ak_symbol = symbol.replace('.SZ', '')
    else:
        raise ValueError(f"无效股票代码: {symbol}")

    try:
        # 获取前复权数据
        df = ak.stock_zh_a_hist(
            symbol=ak_symbol,
            period="daily",
            start_date=(datetime.now() - timedelta(days=days+30)).strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d"),
            adjust="qfq"  # 前复权
        )

        if df is None or df.empty:
            return pd.DataFrame()

        # 重命名字段以匹配Qlib格式
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'money'
        })

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df[['open', 'high', 'low', 'close', 'volume', 'money']]

        # 只取最近N天
        df = df.tail(days)

        return df

    except Exception as e:
        print(f"  ⚠️ 获取前复权数据失败: {e}")
        return pd.DataFrame()


def verify_alignment(symbol: str, name: str, data_dir: Path) -> dict:
    """
    验证单只股票的对齐情况

    返回验证结果字典
    """
    result = {
        'symbol': symbol,
        'name': name,
        'status': 'unknown',
        'details': {}
    }

    # 1. 获取实时行情（真实价格）
    quotes = get_realtime_quotes([symbol])

    if not quotes:
        result['status'] = 'error'
        result['details']['error'] = '无法获取实时行情'
        return result

    quote = quotes[0]
    result['details']['realtime'] = {
        'price': quote['price'],
        'open': quote['open'],
        'high': quote['high'],
        'low': quote['low'],
        'prev_close': quote['prev_close'],
        'timestamp': quote['timestamp']
    }

    # 2. 读取本地前复权数据
    local_df = get_local_data(symbol, data_dir)

    if local_df.empty:
        result['status'] = 'error'
        result['details']['error'] = '本地数据不存在'
        return result

    latest_local = local_df.iloc[-1]
    result['details']['local'] = {
        'date': str(local_df.index[-1])[:10],
        'close': float(latest_local['close']),
        'open': float(latest_local['open']),
        'high': float(latest_local['high']),
        'low': float(latest_local['low'])
    }

    # 3. 获取AKShare前复权最新数据（用于对比）
    print(f"  正在从AKShare获取前复权数据...")
    qfq_df = get_akshare_qfq_data(symbol, days=10)

    if not qfq_df.empty:
        latest_qfq = qfq_df.iloc[-1]
        result['details']['akshare_qfq'] = {
            'date': str(qfq_df.index[-1])[:10],
            'close': float(latest_qfq['close']),
            'open': float(latest_qfq['open'])
        }

        # 计算AKShare前复权数据与本地数据的差异
        local_date = result['details']['local']['date']

        if local_date in [str(d)[:10] for d in qfq_df.index]:
            qfq_row = qfq_df.loc[qfq_df.index.astype(str).str[:10] == local_date].iloc[0]
            price_diff = abs(float(qfq_row['close']) - result['details']['local']['close'])
            price_diff_pct = (price_diff / result['details']['local']['close']) * 100

            result['details']['local_vs_akshare'] = {
                'price_diff': price_diff,
                'price_diff_pct': price_diff_pct,
                'aligned': price_diff_pct < 0.01  # 差异小于0.01%视为对齐
            }

    # 4. 分析价格连续性（是否有除权除息）
    local_close = result['details']['local']['close']
    realtime_prev_close = quote['prev_close']

    # 计算理论涨跌幅
    days_gap = (datetime.now().date() - pd.to_datetime(result['details']['local']['date']).date()).days

    result['details']['continuity'] = {
        'days_gap': days_gap,
        'local_close': local_close,
        'realtime_prev_close': realtime_prev_close,
        'price_gap': abs(local_close - realtime_prev_close),
        'price_gap_pct': abs((local_close / realtime_prev_close - 1) * 100) if realtime_prev_close > 0 else 0
    }

    # 判断是否有除权除息事件
    # 如果本地收盘价与实时昨收差异 > 10%，可能存在除权
    has_adjustment = result['details']['continuity']['price_gap_pct'] > 10
    result['details']['continuity']['likely_adjustment'] = has_adjustment

    # 5. 综合判断对齐状态
    if has_adjustment:
        result['status'] = 'warning'
        result['details']['conclusion'] = '检测到可能的除权除息事件，复权价格与真实价格存在差异'
    else:
        result['status'] = 'ok'
        result['details']['conclusion'] = '价格连续性正常，本地复权数据与实时行情对齐'

    return result


def main():
    """主函数"""
    # 股票列表
    test_stocks = [
        ('000001.SZ', '平安银行'),
        ('600519.SH', '贵州茅台'),
        ('300750.SZ', '宁德时代'),
        ('601318.SH', '中国平安'),
        ('000858.SZ', '五粮液'),
    ]

    # 数据目录
    data_dir = Path.home() / '.qlib' / 'qlib_data' / 'cn_data'

    print("=" * 80)
    print("实时行情与复权数据对齐验证报告")
    print("=" * 80)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据目录: {data_dir}")
    print(f"验证股票数: {len(test_stocks)}")
    print("=" * 80)
    print()

    results = []

    for symbol, name in test_stocks:
        print(f"📊 验证: {name} ({symbol})")

        result = verify_alignment(symbol, name, data_dir)
        results.append(result)

        # 打印结果
        if result['status'] == 'error':
            print(f"  ❌ 错误: {result['details'].get('error', '未知错误')}")
        else:
            details = result['details']

            # 实时行情
            if 'realtime' in details:
                rt = details['realtime']
                print(f"  📈 实时行情（真实价格）:")
                print(f"     开盘: ¥{rt['open']:.2f} | 现价: ¥{rt['price']:.2f}")
                print(f"     昨收: ¥{rt['prev_close']:.2f} | 时间: {rt['timestamp']}")

            # 本地数据
            if 'local' in details:
                local = details['local']
                print(f"  💾 本地数据（前复权）:")
                print(f"     日期: {local['date']} | 收盘: ¥{local['close']:.2f}")

            # AKShare对比
            if 'local_vs_akshare' in details:
                comp = details['local_vs_akshare']
                status = "✓" if comp['aligned'] else "⚠️"
                print(f"  {status} 本地 vs AKShare: 差异 {comp['price_diff_pct']:.4f}%")

            # 连续性分析
            if 'continuity' in details:
                cont = details['continuity']
                days = cont['days_gap']
                gap_pct = cont['price_gap_pct']

                if cont['likely_adjustment']:
                    print(f"  ⚠️  价格连续性: 检测到可能的除权事件（差异 {gap_pct:.2f}%）")
                    print(f"      本地收盘 ¥{cont['local_close']:.2f} vs 实时昨收 ¥{cont['realtime_prev_close']:.2f}")
                else:
                    print(f"  ✓ 价格连续性: 正常（{days}天间隔，差异 {gap_pct:.2f}%）")

            # 结论
            status_icon = {'ok': '✅', 'warning': '⚠️', 'error': '❌'}
            print(f"  {status_icon.get(result['status'], '❓')} 结论: {details.get('conclusion', '未知')}")

        print()

    # 统计总结
    print("=" * 80)
    print("验证总结")
    print("=" * 80)

    ok_count = sum(1 for r in results if r['status'] == 'ok')
    warning_count = sum(1 for r in results if r['status'] == 'warning')
    error_count = sum(1 for r in results if r['status'] == 'error')

    print(f"✅ 对齐正常: {ok_count}/{len(results)}")
    print(f"⚠️  检测到异常: {warning_count}/{len(results)}")
    print(f"❌ 验证错误: {error_count}/{len(results)}")

    print()
    print("💡 说明:")
    print("   - 本地数据使用前复权（qfq），实时行情为真实交易价格")
    print("   - 如果期间发生除权除息，两者会存在价格差异")
    print("   - 前复权数据会向前调整历史价格，使价格连续可比")
    print("=" * 80)


if __name__ == '__main__':
    main()
