#!/usr/bin/env python3
"""
Streamlit 后端模块测试

验证所有后端模块能否正常工作

运行：python test_streamlit_backend.py
"""

import sys
from pathlib import Path

print("=" * 60)
print("Streamlit 后端模块测试")
print("=" * 60)

# ===== 测试1: 导入检查 =====
print("\n[测试1] 检查模块导入...")

try:
    from backend.config import (
        DATA_DIR, CACHE_DIR, DAILY_DIR, PORTFOLIO_DIR,
        DEFAULT_BUDGET, DEFAULT_TOP_N
    )
    print("✓ backend.config 导入成功")
except Exception as e:
    print(f"❌ backend.config 导入失败: {e}")
    sys.exit(1)

try:
    from backend.selector_api import get_daily_selection
    print("✓ backend.selector_api 导入成功")
except Exception as e:
    print(f"❌ backend.selector_api 导入失败: {e}")
    sys.exit(1)

try:
    from backend.portfolio_manager import VirtualPortfolio
    print("✓ backend.portfolio_manager 导入成功")
except Exception as e:
    print(f"❌ backend.portfolio_manager 导入失败: {e}")
    sys.exit(1)

try:
    from backend.data_access import DataAccess
    print("✓ backend.data_access 导入成功")
except Exception as e:
    print(f"❌ backend.data_access 导入失败: {e}")
    sys.exit(1)

# ===== 测试2: 配置检查 =====
print("\n[测试2] 检查配置...")

print(f"  DATA_DIR: {DATA_DIR}")
print(f"  CACHE_DIR: {CACHE_DIR}")
print(f"  DAILY_DIR: {DAILY_DIR}")
print(f"  PORTFOLIO_DIR: {PORTFOLIO_DIR}")
print(f"  DEFAULT_BUDGET: {DEFAULT_BUDGET}")
print(f"  DEFAULT_TOP_N: {DEFAULT_TOP_N}")

# 检查目录是否存在
for directory in [DATA_DIR, CACHE_DIR, DAILY_DIR, PORTFOLIO_DIR]:
    if directory.exists():
        print(f"✓ {directory.name}/ 目录存在")
    else:
        print(f"⚠️ {directory.name}/ 目录不存在（将自动创建）")

# ===== 测试3: 数据访问 =====
print("\n[测试3] 测试数据访问...")

try:
    data = DataAccess()
    print("✓ DataAccess 实例化成功")

    summary = data.get_summary_stats()
    print(f"  总选股次数: {summary['total_selections']}")
    print(f"  最新日期: {summary.get('latest_selection_date', '无')}")
    print(f"  持仓存在: {summary['has_portfolio']}")
    print(f"  总交易数: {summary['total_trades']}")

    print("✓ 数据访问测试通过")

except Exception as e:
    print(f"❌ 数据访问测试失败: {e}")

# ===== 测试4: 选股API（可选，需要数据） =====
print("\n[测试4] 测试选股API（跳过实际执行，仅验证函数）...")

try:
    # 不实际执行，仅检查函数签名
    import inspect

    sig = inspect.signature(get_daily_selection)
    params = list(sig.parameters.keys())
    print(f"  get_daily_selection 参数: {params}")

    expected_params = ['budget', 'top_n', 'momentum_threshold', 'skip_download', 'force_refresh', 'silent']
    if all(p in params for p in expected_params):
        print("✓ 选股API参数正确")
    else:
        print("⚠️ 选股API参数可能不完整")

except Exception as e:
    print(f"❌ 选股API检查失败: {e}")

# ===== 测试5: 持仓管理（创建测试持仓） =====
print("\n[测试5] 测试持仓管理...")

try:
    # 创建临时测试持仓
    portfolio = VirtualPortfolio(initial_cash=100000, load_existing=False)
    print(f"✓ VirtualPortfolio 创建成功（初始资金: {portfolio.cash:.0f}）")

    # 测试买入（如果有数据）
    try:
        portfolio.buy('002920.SZ', 100, 153.0, '德赛西威', date='2025-01-15')
        print(f"✓ 买入测试成功（剩余资金: {portfolio.cash:.0f}）")

        # 测试获取统计
        stats = portfolio.get_stats(date='2025-01-15')
        print(f"  总市值: {stats['total_value']:.0f}")
        print(f"  持仓数: {len(stats['positions'])}")

        # 清理测试数据
        portfolio.reset(cash=100000)
        print("✓ 测试数据已清理")

    except Exception as e:
        print(f"⚠️ 买入测试跳过（可能缺少股票数据）: {e}")

except Exception as e:
    print(f"❌ 持仓管理测试失败: {e}")

# ===== 测试6: UI组件导入 =====
print("\n[测试6] 检查UI组件导入...")

try:
    from components.stock_table import render_selection_table, render_portfolio_table
    print("✓ components.stock_table 导入成功")
except Exception as e:
    print(f"❌ components.stock_table 导入失败: {e}")

try:
    from components.portfolio_chart import render_summary_metrics
    print("✓ components.portfolio_chart 导入成功")
except Exception as e:
    print(f"❌ components.portfolio_chart 导入失败: {e}")

# ===== 总结 =====
print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)

print("\n📋 下一步:")
print("1. 如果所有测试通过 ✓，运行: streamlit run app.py")
print("2. 如果有警告 ⚠️，检查对应模块是否需要初始化数据")
print("3. 如果有失败 ❌，检查错误信息并修复")

print("\n💡 提示:")
print("- 首次运行建议先执行选股: python scripts/hs300_selector.py")
print("- 这将创建 data/daily/ 目录和选股结果")
print("- 然后再启动 Streamlit UI")
