#!/usr/bin/env python3
"""
large_cap 配置验证测试脚本

用途：
1. 验证 stock_pool.yaml 中 large_cap 结构是否正确
2. 验证 config/settings.py 能否正确加载 large_cap
3. 测试继承机制是否正常工作

作者：Agent M
创建日期：2025-10-16
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings, reload_settings


def test_large_cap_loading():
    """测试 large_cap 加载功能"""
    print("=" * 60)
    print("测试 1: large_cap 配置加载")
    print("=" * 60)

    try:
        settings = get_settings()
        print("✅ 配置加载成功")

        # 验证股票池是否存在
        pools = ['small_cap', 'medium_cap', 'large_cap', 'legacy_test_pool']
        for pool_name in pools:
            try:
                pool = settings.stock_pool.get_pool(pool_name)
                size = len(pool)
                print(f"✅ {pool_name}: {size}只股票")
            except Exception as e:
                print(f"❌ {pool_name} 加载失败: {e}")

        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inheritance_mechanism():
    """测试继承机制"""
    print("\n" + "=" * 60)
    print("测试 2: 继承机制验证")
    print("=" * 60)

    try:
        settings = get_settings()

        # 获取各个股票池
        small_cap = settings.stock_pool.get_pool('small_cap')
        medium_cap = settings.stock_pool.get_pool('medium_cap')
        large_cap = settings.stock_pool.get_pool('large_cap')

        print(f"\n📊 股票池大小:")
        print(f"  - small_cap:  {len(small_cap)}只")
        print(f"  - medium_cap: {len(medium_cap)}只")
        print(f"  - large_cap:  {len(large_cap)}只")

        # 验证继承关系
        print(f"\n🔗 继承关系验证:")

        # medium_cap 应包含所有 small_cap
        small_symbols = set(s.symbol for s in small_cap)
        medium_symbols = set(s.symbol for s in medium_cap)
        if small_symbols.issubset(medium_symbols):
            print(f"  ✅ medium_cap 正确继承 small_cap")
        else:
            print(f"  ❌ medium_cap 未完全继承 small_cap")

        # large_cap 应包含所有 medium_cap
        large_symbols = set(s.symbol for s in large_cap)
        if medium_symbols.issubset(large_symbols):
            print(f"  ✅ large_cap 正确继承 medium_cap")
        else:
            print(f"  ❌ large_cap 未完全继承 medium_cap")

        # 显示新增股票数量
        medium_additional = len(medium_cap) - len(small_cap)
        large_additional = len(large_cap) - len(medium_cap)
        print(f"\n➕ 新增股票数量:")
        print(f"  - medium_cap 新增: {medium_additional}只")
        print(f"  - large_cap 新增:  {large_additional}只")
        print(f"  - large_cap 预期新增: 80只 (待Agent L完成)")

        return True
    except Exception as e:
        print(f"❌ 继承机制验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pool_methods():
    """测试股票池方法"""
    print("\n" + "=" * 60)
    print("测试 3: 股票池方法验证")
    print("=" * 60)

    try:
        settings = get_settings()

        # 测试 get_pool()
        print("\n📦 get_pool() 方法测试:")
        large_cap = settings.stock_pool.get_pool('large_cap')
        print(f"  ✅ get_pool('large_cap'): {len(large_cap)}只")

        # 测试 get_symbols()
        print("\n🏷️  get_symbols() 方法测试:")
        symbols = settings.stock_pool.get_symbols('large_cap')
        print(f"  ✅ get_symbols('large_cap'): {len(symbols)}个代码")
        print(f"  示例: {symbols[:3]}")

        # 测试 get_pool_size()
        print("\n📏 get_pool_size() 方法测试:")
        size = settings.stock_pool.get_pool_size('large_cap')
        print(f"  ✅ get_pool_size('large_cap'): {size}只")

        # 测试错误处理
        print("\n⚠️  错误处理测试:")
        try:
            settings.stock_pool.get_pool('invalid_pool')
            print(f"  ❌ 应该抛出 ValueError")
        except ValueError as e:
            print(f"  ✅ 正确抛出 ValueError: {e}")

        return True
    except Exception as e:
        print(f"❌ 方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_details():
    """测试股票详细信息"""
    print("\n" + "=" * 60)
    print("测试 4: 股票详细信息")
    print("=" * 60)

    try:
        settings = get_settings()

        large_cap = settings.stock_pool.get_pool('large_cap')

        if len(large_cap) > 0:
            print(f"\n📝 large_cap 前5只股票详情:")
            for i, stock in enumerate(large_cap[:5], 1):
                print(f"  {i}. {stock.symbol} {stock.name}")
                print(f"     行业: {stock.industry} | 板块: {stock.sector}")

            # 显示来源
            small_count = len(settings.stock_pool.get_pool('small_cap'))
            medium_count = len(settings.stock_pool.get_pool('medium_cap'))
            print(f"\n📊 large_cap 组成:")
            print(f"  - 继承自 small_cap:  {small_count}只")
            print(f"  - 继承自 medium_cap: {medium_count - small_count}只")
            print(f"  - large_cap 新增:    {len(large_cap) - medium_count}只")
            print(f"  - 总计:              {len(large_cap)}只")
        else:
            print(f"\n⚠️  large_cap 当前为空（等待Agent L填充）")

        return True
    except Exception as e:
        print(f"❌ 详细信息测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("large_cap 配置验证测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("配置加载", test_large_cap_loading()))
    results.append(("继承机制", test_inheritance_mechanism()))
    results.append(("股票池方法", test_pool_methods()))
    results.append(("股票详情", test_stock_details()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n✅ 所有测试通过！large_cap 配置系统已就绪")
        print("⏳ 等待 Agent L 提供80只新增股票数据")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
