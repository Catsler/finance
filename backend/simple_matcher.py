#!/usr/bin/env python3
"""
Stage 1 MVP: 简化撮合引擎

基于日线K线的保守撮合逻辑：
1. 限价单：价格必须满足 low <= 买入限价 或 high >= 卖出限价
2. 止损单：触发后按"触发价 × (1-滑点)"成交
3. 涨跌停板：涨停无法买入，跌停无法卖出
4. 成交量限制：单笔不超过当日成交量的10%

重要假设：
- 使用日线数据模拟，无法精确反映盘中时机
- 保守估计：宁可低估收益，也不过度乐观

作者: Claude Code
日期: 2025-01-10
版本: v1.0 (Stage 1 MVP)
"""

from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from backend.basic_orders import LimitOrder, StopOrder, Trade


class SimpleConservativeMatcher:
    """
    简化保守撮合引擎

    设计原则：
    1. 保守估计：避免过度乐观的成交假设
    2. 可配置：所有阈值从配置文件读取
    3. 最小化：只实现必需逻辑

    配置参数：
    - stop_slippage: 止损滑点（默认2%）
    - limit_buffer: 限价缓冲（默认0.5%）
    - max_volume_pct: 最大成交量比例（默认10%）
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化撮合引擎

        Args:
            config: 配置字典（如果None，使用默认值）
        """
        if config is None:
            # 尝试从配置文件加载
            config_path = Path(__file__).parent.parent / 'config' / 'stage1_params.yaml'
            if HAS_YAML and config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = yaml.safe_load(f)
                    config = full_config.get('matching', {})
            else:
                config = {}

        # 加载配置（带默认值）
        self.stop_slippage = config.get('stop_slippage', 0.02)
        self.limit_buffer = config.get('limit_buffer', 0.005)
        self.max_volume_pct = config.get('max_volume_pct', 0.10)

        # 佣金配置
        commission_config = config.get('commission', {}) if 'commission' in config else {}
        self.commission_rate = commission_config.get('rate', 0.0003)
        self.min_commission = commission_config.get('minimum', 5.0)
        self.stamp_tax = commission_config.get('stamp_tax', 0.001)

    def match_limit(self, order: LimitOrder, bar: Dict) -> Optional[Trade]:
        """
        撮合限价单

        Args:
            order: 限价单
            bar: 日K线数据
                {
                    'date': '2023-01-10',
                    'open': 11.50,
                    'high': 11.80,
                    'low': 11.40,
                    'close': 11.70,
                    'volume': 100000,
                    'prev_close': 11.45
                }

        Returns:
            Trade对象（成交）或 None（未成交）
        """
        # 保守估计：价格必须明显满足条件
        if order.direction == 'buy':
            # 买入：最低价*(1+buffer) <= 限价，才认为有成交机会
            # 保守：考虑最低价可能向上波动buffer
            if bar['low'] * (1 + self.limit_buffer) > order.limit_price:
                return None  # 价格不满足
            fill_price = order.limit_price
        else:
            # 卖出：最高价*(1-buffer) >= 限价
            # 保守：考虑最高价可能向下波动buffer
            if bar['high'] * (1 - self.limit_buffer) < order.limit_price:
                return None
            fill_price = order.limit_price

        # 检查涨跌停板
        if self._is_limit_board(bar, order.direction):
            return None

        # 成交量限制
        fill_quantity = self._apply_volume_limit(order.quantity, bar['volume'])
        if fill_quantity < 100:  # 不足1手
            return None

        # 生成成交记录
        return Trade(
            order_id=order.order_id,
            symbol=order.symbol,
            direction=order.direction,
            fill_price=fill_price,
            fill_quantity=fill_quantity,
            fill_time=self._estimate_fill_time(bar['date'], 'limit'),
            commission=self._calc_commission(fill_price, fill_quantity, order.direction),
            fill_type='limit'
        )

    def match_stop(self, order: StopOrder, bar: Dict) -> Optional[Trade]:
        """
        撮合止损单

        Args:
            order: 止损单
            bar: 日K线数据

        Returns:
            Trade对象（成交）或 None（未触发）
        """
        # 检查是否触发
        if order.direction == 'sell':
            # 止损卖出：最低价 <= 触发价
            if bar['low'] > order.trigger_price:
                return None  # 未触发
        else:
            # 止损买入（少见）：最高价 >= 触发价
            if bar['high'] < order.trigger_price:
                return None

        # 悲观估计：触发后价格继续向不利方向移动
        if order.direction == 'sell':
            fill_price = order.trigger_price * (1 - self.stop_slippage)
        else:
            fill_price = order.trigger_price * (1 + self.stop_slippage)

        # 检查涨跌停板
        if self._is_limit_board(bar, order.direction):
            return None  # 涨跌停无法成交

        # 成交量限制
        fill_quantity = self._apply_volume_limit(order.quantity, bar['volume'])
        if fill_quantity < 100:
            return None

        return Trade(
            order_id=order.order_id,
            symbol=order.symbol,
            direction=order.direction,
            fill_price=fill_price,
            fill_quantity=fill_quantity,
            fill_time=self._estimate_fill_time(bar['date'], 'stop'),
            commission=self._calc_commission(fill_price, fill_quantity, order.direction),
            fill_type='stop'
        )

    def _is_limit_board(self, bar: Dict, direction: str) -> bool:
        """
        检查涨跌停板

        判断标准：
        - 涨停：涨幅 >= 9.5% 且收盘价 = 最高价
        - 跌停：跌幅 <= -9.5% 且收盘价 = 最低价
        """
        pct_change = (bar['close'] / bar['prev_close']) - 1

        if direction == 'buy':
            # 涨停板无法买入
            return pct_change >= 0.095 and bar['close'] == bar['high']
        else:
            # 跌停板无法卖出
            return pct_change <= -0.095 and bar['close'] == bar['low']

    def _apply_volume_limit(self, quantity: int, daily_volume: int) -> int:
        """
        应用成交量限制

        规则：单笔不超过当日成交量的X%
        """
        max_quantity = int(daily_volume * self.max_volume_pct)
        return min(quantity, max_quantity)

    def _calc_commission(self, price: float, quantity: int, direction: str) -> float:
        """
        计算佣金

        规则：
        - 佣金：成交金额 × 费率（买卖双向）
        - 最低佣金：通常5元
        - 印花税：成交金额 × 千一（仅卖出）
        """
        amount = price * quantity

        # 佣金
        commission = amount * self.commission_rate
        commission = max(commission, self.min_commission)

        # 印花税（仅卖出）
        if direction == 'sell':
            stamp_tax = amount * self.stamp_tax
            commission += stamp_tax

        return commission

    def _estimate_fill_time(self, date: str, fill_type: str) -> datetime:
        """
        估算成交时间（简化）

        规则：
        - 限价单：开盘后5分钟（09:35:00）
        - 止损单：盘中触发（假设11:00:00）
        """
        if fill_type == 'stop':
            return datetime.strptime(f"{date} 11:00:00", "%Y-%m-%d %H:%M:%S")
        else:
            return datetime.strptime(f"{date} 09:35:00", "%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    # 简单测试
    print("=== 测试撮合引擎 ===")

    matcher = SimpleConservativeMatcher()
    print(f"配置: 止损滑点={matcher.stop_slippage}, 限价缓冲={matcher.limit_buffer}")

    # 测试数据
    bar = {
        'date': '2023-01-10',
        'open': 11.50,
        'high': 11.80,
        'low': 11.40,
        'close': 11.70,
        'volume': 100000,
        'prev_close': 11.45
    }

    print("\n=== 测试1: 限价买入（成交） ===")
    order1 = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=11.45  # 限价11.45，低点11.40，应该成交
    )
    trade1 = matcher.match_limit(order1, bar)
    if trade1:
        print(f"✅ 成交: {trade1.fill_quantity}股 @ ¥{trade1.fill_price} (佣金¥{trade1.commission:.2f})")
    else:
        print("❌ 未成交")

    print("\n=== 测试2: 限价买入（未成交） ===")
    order2 = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=11.30  # 限价11.30，低点11.40，价格不满足
    )
    trade2 = matcher.match_limit(order2, bar)
    if trade2:
        print(f"✅ 成交")
    else:
        print("❌ 未成交（价格不满足）")

    print("\n=== 测试3: 止损卖出（触发） ===")
    order3 = StopOrder(
        symbol='000001.SZ',
        direction='sell',
        quantity=1000,
        trigger_price=11.50  # 触发价11.50，低点11.40，已触发
    )
    trade3 = matcher.match_stop(order3, bar)
    if trade3:
        print(f"✅ 止损触发: {trade3.fill_quantity}股 @ ¥{trade3.fill_price:.2f} (含滑点)")
        print(f"   触发价¥{order3.trigger_price} → 成交价¥{trade3.fill_price:.2f} (滑点{matcher.stop_slippage*100}%)")
    else:
        print("❌ 未触发")

    print("\n=== 测试4: 涨停板（无法买入） ===")
    limit_up_bar = {
        'date': '2023-01-11',
        'open': 12.60,
        'high': 12.60,
        'low': 12.60,
        'close': 12.60,
        'volume': 100000,
        'prev_close': 11.45  # +10.04%涨停
    }
    order4 = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=12.55
    )
    trade4 = matcher.match_limit(order4, limit_up_bar)
    if trade4:
        print(f"✅ 成交")
    else:
        print("❌ 未成交（涨停板无法买入）")
