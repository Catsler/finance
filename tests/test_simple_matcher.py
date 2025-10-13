#!/usr/bin/env python3
"""
Stage 1 MVP: 撮合引擎单元测试

测试覆盖：
1. 限价单成交/未成交
2. 止损单触发/未触发
3. 涨跌停板检测
4. 成交量限制
5. 佣金计算

运行方式：
    pytest tests/test_simple_matcher.py -v
    或
    python tests/test_simple_matcher.py

作者: Claude Code
日期: 2025-01-10
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.simple_matcher import SimpleConservativeMatcher
from backend.basic_orders import LimitOrder, StopOrder


def test_limit_buy_success():
    """测试限价买入成交"""
    matcher = SimpleConservativeMatcher()

    bar = {
        'date': '2023-01-10',
        'open': 11.50,
        'high': 11.80,
        'low': 11.35,  # 更低的低点，确保满足保守估计
        'close': 11.70,
        'volume': 100000,
        'prev_close': 11.45
    }

    order = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=11.45  # 11.35 * 1.005 = 11.407 < 11.45，满足条件
    )

    trade = matcher.match_limit(order, bar)

    assert trade is not None, "限价买入应该成交"
    assert trade.fill_price == 11.45, f"成交价应该是11.45，实际{trade.fill_price}"
    assert trade.fill_quantity == 1000, "成交数量应该是1000"
    assert trade.direction == 'buy'
    print("✅ 测试通过: 限价买入成交")


def test_limit_buy_fail_price():
    """测试限价买入因价格不满足而未成交"""
    matcher = SimpleConservativeMatcher()

    bar = {
        'date': '2023-01-10',
        'open': 11.50,
        'high': 11.80,
        'low': 11.40,
        'close': 11.70,
        'volume': 100000,
        'prev_close': 11.45
    }

    order = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=11.30  # 低点11.40，价格不满足
    )

    trade = matcher.match_limit(order, bar)

    assert trade is None, "限价太低，应该未成交"
    print("✅ 测试通过: 限价买入未成交（价格不满足）")


def test_stop_sell_triggered():
    """测试止损卖出触发"""
    matcher = SimpleConservativeMatcher()

    bar = {
        'date': '2023-01-10',
        'open': 11.50,
        'high': 11.80,
        'low': 11.40,
        'close': 11.70,
        'volume': 100000,
        'prev_close': 11.45
    }

    order = StopOrder(
        symbol='000001.SZ',
        direction='sell',
        quantity=1000,
        trigger_price=11.50  # 低点11.40 < 触发价11.50，应触发
    )

    trade = matcher.match_stop(order, bar)

    assert trade is not None, "止损应该触发"
    assert trade.fill_price < order.trigger_price, "止损成交价应低于触发价（含滑点）"
    # 验证滑点：11.50 * (1 - 0.02) = 11.27
    expected_price = order.trigger_price * (1 - matcher.stop_slippage)
    assert abs(trade.fill_price - expected_price) < 0.01, f"滑点计算错误：期望{expected_price}，实际{trade.fill_price}"
    print(f"✅ 测试通过: 止损触发（触发价¥{order.trigger_price} → 成交价¥{trade.fill_price:.2f}）")


def test_stop_sell_not_triggered():
    """测试止损未触发"""
    matcher = SimpleConservativeMatcher()

    bar = {
        'date': '2023-01-10',
        'open': 11.50,
        'high': 11.80,
        'low': 11.40,
        'close': 11.70,
        'volume': 100000,
        'prev_close': 11.45
    }

    order = StopOrder(
        symbol='000001.SZ',
        direction='sell',
        quantity=1000,
        trigger_price=11.30  # 低点11.40 > 触发价11.30，未触发
    )

    trade = matcher.match_stop(order, bar)

    assert trade is None, "止损应该未触发"
    print("✅ 测试通过: 止损未触发")


def test_limit_up_reject_buy():
    """测试涨停板拒绝买入"""
    matcher = SimpleConservativeMatcher()

    # 构造涨停板数据
    limit_up_bar = {
        'date': '2023-01-11',
        'open': 12.60,
        'high': 12.60,
        'low': 12.60,
        'close': 12.60,
        'volume': 100000,
        'prev_close': 11.45  # +10.04%涨停
    }

    order = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=12.55
    )

    trade = matcher.match_limit(order, limit_up_bar)

    assert trade is None, "涨停板应该拒绝买入"
    print("✅ 测试通过: 涨停板拒绝买入")


def test_limit_down_reject_sell():
    """测试跌停板拒绝卖出"""
    matcher = SimpleConservativeMatcher()

    # 构造跌停板数据
    limit_down_bar = {
        'date': '2023-01-11',
        'open': 10.30,
        'high': 10.30,
        'low': 10.30,
        'close': 10.30,
        'volume': 100000,
        'prev_close': 11.45  # -10.04%跌停
    }

    order = StopOrder(
        symbol='000001.SZ',
        direction='sell',
        quantity=1000,
        trigger_price=10.50  # 已触发，但跌停无法卖出
    )

    trade = matcher.match_stop(order, limit_down_bar)

    assert trade is None, "跌停板应该拒绝卖出"
    print("✅ 测试通过: 跌停板拒绝卖出")


def test_volume_limit():
    """测试成交量限制"""
    matcher = SimpleConservativeMatcher()

    bar = {
        'date': '2023-01-10',
        'open': 11.50,
        'high': 11.80,
        'low': 11.35,  # 确保价格满足
        'close': 11.70,
        'volume': 5000,  # 很小的成交量
        'prev_close': 11.45
    }

    order = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=10000,  # 远超成交量
        limit_price=11.50
    )

    trade = matcher.match_limit(order, bar)

    # 成交量应该被限制为 5000 * 0.10 = 500股
    expected_max = int(bar['volume'] * matcher.max_volume_pct)
    if expected_max >= 100:
        # 超过1手，应该成交
        assert trade is not None, f"应该成交（限制后{expected_max}股 >= 100股）"
        assert trade.fill_quantity == expected_max, f"成交量应被限制在{expected_max}股，实际{trade.fill_quantity}"
        print(f"✅ 测试通过: 成交量限制（委托{order.quantity}股 → 实际{trade.fill_quantity}股）")
    else:
        # 不足1手，应该拒绝
        assert trade is None, f"成交量不足1手（{expected_max}股），应拒绝"
        print("✅ 测试通过: 成交量不足1手，拒绝成交")


def test_commission_calculation():
    """测试佣金计算"""
    matcher = SimpleConservativeMatcher()

    bar = {
        'date': '2023-01-10',
        'open': 11.50,
        'high': 11.80,
        'low': 11.35,  # 确保价格满足
        'close': 11.70,
        'volume': 100000,
        'prev_close': 11.45
    }

    # 测试买入佣金
    buy_order = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=11.45
    )
    buy_trade = matcher.match_limit(buy_order, bar)

    assert buy_trade is not None, "买入订单应该成交"
    # 佣金 = max(11450 * 0.0003, 5.0) = 5.0元（最低佣金）
    assert buy_trade.commission >= matcher.min_commission, "佣金应不低于最低佣金"
    print(f"✅ 测试通过: 买入佣金计算（¥{buy_trade.commission:.2f}）")

    # 测试卖出佣金（含印花税）
    sell_order = LimitOrder(
        symbol='000001.SZ',
        direction='sell',
        quantity=1000,
        limit_price=11.70  # 11.80 * (1-0.005) = 11.741 >= 11.70，满足条件
    )
    sell_trade = matcher.match_limit(sell_order, bar)

    assert sell_trade is not None, "卖出订单应该成交"
    # 卖出佣金应高于买入佣金（含印花税）
    assert sell_trade.commission > buy_trade.commission, f"卖出佣金（¥{sell_trade.commission:.2f}）应高于买入（¥{buy_trade.commission:.2f}，含印花税）"
    print(f"✅ 测试通过: 卖出佣金计算（¥{sell_trade.commission:.2f}，含印花税）")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Stage 1 MVP: 撮合引擎单元测试")
    print("=" * 60)
    print()

    tests = [
        test_limit_buy_success,
        test_limit_buy_fail_price,
        test_stop_sell_triggered,
        test_stop_sell_not_triggered,
        test_limit_up_reject_buy,
        test_limit_down_reject_sell,
        test_volume_limit,
        test_commission_calculation,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {test_func.__name__}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {test_func.__name__}")
            print(f"   异常: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"测试结果: {passed}通过, {failed}失败, 共{passed+failed}个测试")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
