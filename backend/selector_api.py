#!/usr/bin/env python3
"""
选股逻辑API封装 - 供Streamlit调用

设计原则：
1. 零修改原脚本 - 直接复用scripts/hs300_selector.py
2. 屏蔽输出 - 捕获print输出，转为日志（可选）
3. 统一接口 - 提供简洁的API

使用示例：
    from backend.selector_api import get_daily_selection

    result = get_daily_selection(budget=100000, top_n=5)
    print(result['allocation']['positions'])
"""

import sys
from io import StringIO
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

# 添加scripts到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# 导入现有选股逻辑
from hs300_selector import (
    fetch_hs300_constituents,
    filter_by_momentum,
    allocate_equal_weight,
    validate_budget
)

from backend.config import (
    DEFAULT_BUDGET,
    DEFAULT_TOP_N,
    DEFAULT_MOMENTUM_THRESHOLD
)


@contextmanager
def suppress_prints():
    """
    临时屏蔽print输出

    上下文管理器，用于在调用原脚本时屏蔽控制台输出
    """
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield
    finally:
        sys.stdout = old_stdout


def get_daily_selection(
    budget=DEFAULT_BUDGET,
    top_n=DEFAULT_TOP_N,
    momentum_threshold=DEFAULT_MOMENTUM_THRESHOLD,
    skip_download=True,
    force_refresh=False,
    silent=True
):
    """
    获取每日选股结果（API接口）

    Args:
        budget: 总预算（元）
        top_n: 候选池大小
        momentum_threshold: 20日涨幅阈值（百分比）
        skip_download: 跳过数据下载（默认True，假设数据已存在）
        force_refresh: 强制刷新成分股列表
        silent: 是否屏蔽print输出（默认True）

    Returns:
        dict: {
            'constituents': dict,        # 成分股字典 {symbol: name}
            'selected': list,            # 筛选后的股票列表
            'allocation': dict,          # 仓位分配结果
            'metadata': dict,            # 元数据（参数、时间戳等）
            'stats': dict                # 统计信息
        }

    Raises:
        ValueError: 预算不足
    """
    # 预算校验（不屏蔽，需要抛出异常）
    validate_budget(budget, top_n)

    # 执行选股逻辑（可选择屏蔽输出）
    if silent:
        with suppress_prints():
            constituents = fetch_hs300_constituents(force_refresh=force_refresh)
            selected = filter_by_momentum(constituents, momentum_threshold)
            allocation = allocate_equal_weight(selected, budget, top_n)
    else:
        constituents = fetch_hs300_constituents(force_refresh=force_refresh)
        selected = filter_by_momentum(constituents, momentum_threshold)
        allocation = allocate_equal_weight(selected, budget, top_n)

    # 构造返回结果
    return {
        'constituents': constituents,
        'selected': selected,
        'allocation': allocation,
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'budget': budget,
            'top_n': top_n,
            'momentum_threshold': momentum_threshold,
            'skip_download': skip_download,
            'force_refresh': force_refresh
        },
        'stats': {
            'constituents_count': len(constituents),
            'selected_count': len(selected),
            'position_count': len(allocation.get('positions', [])),
            'unaffordable_count': len(allocation.get('unaffordable', []))
        }
    }


def get_top_candidates(result, limit=10):
    """
    从选股结果中提取Top候选列表

    Args:
        result: get_daily_selection()的返回值
        limit: 返回前N只候选

    Returns:
        list: [{symbol, name, return_20d, close, ma5, ma10}, ...]
    """
    selected = result['selected']
    return selected[:limit]


def get_allocation_summary(result):
    """
    获取仓位分配摘要

    Args:
        result: get_daily_selection()的返回值

    Returns:
        dict: {
            'total_cost': float,
            'utilization': float,
            'position_count': int,
            'unaffordable_count': int,
            'warning': str or None
        }
    """
    allocation = result['allocation']

    return {
        'total_cost': allocation.get('total_cost', 0),
        'utilization': allocation.get('utilization', 0),
        'position_count': allocation.get('count', 0),
        'unaffordable_count': len(allocation.get('unaffordable', [])),
        'warning': allocation.get('warning')
    }


def detect_changes(current_result, previous_result):
    """
    检测候选股票变化

    Args:
        current_result: 当前选股结果
        previous_result: 上次选股结果（可为None）

    Returns:
        dict: {
            'new': set,         # 新增候选
            'removed': set,     # 移除候选
            'continued': set    # 持续候选
        }
    """
    current_symbols = {s['symbol'] for s in current_result['selected'][:current_result['metadata']['top_n']]}

    if previous_result is None:
        return {
            'new': current_symbols,
            'removed': set(),
            'continued': set()
        }

    previous_symbols = {s['symbol'] for s in previous_result['selected'][:previous_result['metadata']['top_n']]}

    return {
        'new': current_symbols - previous_symbols,
        'removed': previous_symbols - current_symbols,
        'continued': current_symbols & previous_symbols
    }


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 selector_api.py...\n")

    # 测试1: 静默模式
    print("测试1: 静默模式获取选股")
    result = get_daily_selection(budget=100000, top_n=5, silent=True)
    print(f"✓ 成分股数: {result['stats']['constituents_count']}")
    print(f"✓ 筛选后: {result['stats']['selected_count']}")
    print(f"✓ 持仓数: {result['stats']['position_count']}")
    print(f"✓ 不可负担: {result['stats']['unaffordable_count']}")

    # 测试2: 获取Top候选
    print("\n测试2: Top 3候选")
    top3 = get_top_candidates(result, limit=3)
    for i, stock in enumerate(top3, 1):
        print(f"{i}. {stock['symbol']} {stock['name']} 涨幅:{stock['return_20d']*100:.2f}%")

    # 测试3: 分配摘要
    print("\n测试3: 仓位分配摘要")
    summary = get_allocation_summary(result)
    print(f"总成本: {summary['total_cost']:.0f} 元")
    print(f"利用率: {summary['utilization']:.1f}%")
    print(f"警告: {summary['warning']}")

    print("\n✅ 测试完成")
