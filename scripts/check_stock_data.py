#!/usr/bin/env python3
"""
Phase 6E准备工具：股票数据完整性检查

功能:
    - 检查股票数据是否满足回测要求（时间范围、数据点数）
    - 支持自动替换模式（--auto-fallback）
    - 按状态排序输出（MISSING > INSUFFICIENT > WARNING > OK）

用法:
    # 默认模式（仅提示）
    python scripts/check_stock_data.py

    # 自动替换模式
    python scripts/check_stock_data.py --auto-fallback
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter
import pandas as pd


# 替换方案映射
FALLBACK_MAP = {
    '688981.SH': ('600900.SH', '长江电力', '中芯国际数据不足（科创板）'),
    '002920.SZ': ('601888.SH', '中国中免', '德赛西威流动性偏低'),
}


def check_stock_data_availability(symbols, start_date='2022-01-01',
                                   required_days=600, auto_fallback=False):
    """
    检查股票数据是否满足回测要求

    Args:
        symbols: 待检查的股票代码列表（包含股票信息字典）
        start_date: 起始日期
        required_days: 最少数据天数
        auto_fallback: 是否自动替换问题股票

    Returns:
        results: 检查结果列表
        final_symbols: 最终股票列表（如果auto_fallback=True）
        replacements: 替换记录
    """
    results = []
    final_symbols = []
    replacements = []

    data_dir = Path.home() / '.qlib/qlib_data/cn_data'

    for symbol_info in symbols:
        if isinstance(symbol_info, str):
            symbol = symbol_info
            name = symbol
        else:
            symbol = symbol_info.get('symbol', symbol_info)
            name = symbol_info.get('name', symbol)

        file_path = data_dir / f'{symbol}.csv'

        if not file_path.exists():
            if auto_fallback and symbol in FALLBACK_MAP:
                fallback_symbol, fallback_name, reason = FALLBACK_MAP[symbol]
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'status': 'REPLACED',
                    'reason': '文件不存在',
                    'action': f'自动替换为 {fallback_symbol} ({fallback_name})',
                    'data_points': 0
                })
                final_symbols.append({'symbol': fallback_symbol, 'name': fallback_name})
                replacements.append((symbol, fallback_symbol, reason))
            else:
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'status': 'MISSING',
                    'reason': '文件不存在',
                    'action': f'建议替换为 {FALLBACK_MAP.get(symbol, ("备选", "", ""))[0]}' if symbol in FALLBACK_MAP else '需下载',
                    'data_points': 0
                })
                final_symbols.append({'symbol': symbol, 'name': name})
            continue

        # 读取数据
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])

        # 检查时间范围
        available_data = df[df['date'] >= start_date]
        data_points = len(available_data)

        if data_points < required_days:
            if auto_fallback and symbol in FALLBACK_MAP:
                fallback_symbol, fallback_name, reason = FALLBACK_MAP[symbol]
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'status': 'REPLACED',
                    'reason': f'仅{data_points}条数据，需要{required_days}条',
                    'action': f'自动替换为 {fallback_symbol} ({fallback_name})',
                    'data_points': data_points
                })
                final_symbols.append({'symbol': fallback_symbol, 'name': fallback_name})
                replacements.append((symbol, fallback_symbol, reason))
            else:
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'status': 'INSUFFICIENT',
                    'reason': f'仅{data_points}条数据，需要{required_days}条',
                    'action': f'建议替换为 {FALLBACK_MAP.get(symbol, ("备选", "", ""))[0]}' if symbol in FALLBACK_MAP else '补充数据',
                    'data_points': data_points
                })
                final_symbols.append({'symbol': symbol, 'name': name})
        elif data_points < required_days * 1.1:
            results.append({
                'symbol': symbol,
                'name': name,
                'status': 'WARNING',
                'reason': f'{data_points}条数据，接近最低要求',
                'action': '可用，但建议备选',
                'data_points': data_points
            })
            final_symbols.append({'symbol': symbol, 'name': name})
        else:
            results.append({
                'symbol': symbol,
                'name': name,
                'status': 'OK',
                'reason': f'{data_points}条数据，充足',
                'action': '无需替换',
                'data_points': data_points
            })
            final_symbols.append({'symbol': symbol, 'name': name})

    # 按状态排序
    status_priority = {'MISSING': 0, 'INSUFFICIENT': 1, 'REPLACED': 2, 'WARNING': 3, 'OK': 4}
    results.sort(key=lambda x: (status_priority[x['status']], x['symbol']))

    return results, final_symbols, replacements


def print_check_results(results):
    """打印检查结果（分组显示）"""
    status_count = Counter([r['status'] for r in results])

    print("\n" + "="*80)
    print("股票池扩展数据可用性检查")
    print("="*80)
    print(f"总计: {len(results)}只  |  " +
          f"问题: {status_count.get('MISSING', 0) + status_count.get('INSUFFICIENT', 0)}只  |  " +
          f"替换: {status_count.get('REPLACED', 0)}只  |  " +
          f"警告: {status_count.get('WARNING', 0)}只  |  " +
          f"正常: {status_count.get('OK', 0)}只")
    print("="*80)

    # 分组输出
    current_status = None
    for r in results:
        if r['status'] != current_status:
            current_status = r['status']
            print(f"\n[{current_status}]")

        print(f"  {r['symbol']:<12} {r.get('name', ''):<12} {r['reason']:<40} → {r['action']}")

    print("="*80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='检查股票数据可用性')
    parser.add_argument('--auto-fallback', action='store_true',
                        help='自动替换问题股票（默认仅提示）')
    parser.add_argument('--start-date', default='2022-01-01',
                        help='起始日期（默认2022-01-01）')
    parser.add_argument('--required-days', type=int, default=600,
                        help='最少数据天数（默认600）')
    args = parser.parse_args()

    # 方案B的10只新增股票（激进版，包含科创板）
    new_stocks = [
        {'symbol': '300059.SZ', 'name': '东方财富'},
        {'symbol': '601012.SH', 'name': '隆基绿能'},
        {'symbol': '603288.SH', 'name': '海天味业'},
        {'symbol': '000333.SZ', 'name': '美的集团'},
        {'symbol': '002475.SZ', 'name': '立讯精密'},
        {'symbol': '600309.SH', 'name': '万华化学'},
        {'symbol': '600031.SH', 'name': '三一重工'},
        {'symbol': '300760.SZ', 'name': '迈瑞医疗'},
        {'symbol': '688981.SH', 'name': '中芯国际'},  # 科创板，可能数据不足
        {'symbol': '002920.SZ', 'name': '德赛西威'},
    ]

    results, final_symbols, replacements = check_stock_data_availability(
        new_stocks,
        start_date=args.start_date,
        required_days=args.required_days,
        auto_fallback=args.auto_fallback
    )

    # 打印结果
    print_check_results(results)

    if args.auto_fallback and replacements:
        print(f"\n{'='*80}")
        print("自动替换执行:")
        for original, fallback, reason in replacements:
            print(f"  {original} → {fallback} ({reason})")
        print(f"{'='*80}")
        print(f"\n最终股票列表已更新，共{len(final_symbols)}只")

        # 保存最终列表到JSON
        output = {
            'symbols': final_symbols,
            'replacements': [
                {'original': r[0], 'fallback': r[1], 'reason': r[2]}
                for r in replacements
            ],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        with open('results/phase6e_final_symbols.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print("✓ 已保存: results/phase6e_final_symbols.json")

    elif not args.auto_fallback and (status_count.get('MISSING', 0) + status_count.get('INSUFFICIENT', 0) > 0):
        print(f"\n{'='*80}")
        print("建议:")
        print("  1. 如果需要自动替换，运行: python scripts/check_stock_data.py --auto-fallback")
        print("  2. 或手动下载缺失股票数据")
        print("  3. 推荐使用方案A（保守版），避免科创板数据问题")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
