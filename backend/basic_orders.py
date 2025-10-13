#!/usr/bin/env python3
"""
Stage 1 MVP: 基础委托单类型

仅包含最核心的两种委托：
1. LimitOrder - 限价单（指定价格买入/卖出）
2. StopOrder - 止损单（触发价卖出）

设计原则：
- 最小化：只保留必需字段
- 不可变：使用dataclass冻结，避免运行时修改
- 类型安全：使用类型提示

作者: Claude Code
日期: 2025-01-10
版本: v1.0 (Stage 1 MVP)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


def generate_order_id() -> str:
    """生成唯一订单ID"""
    return str(uuid.uuid4())[:8]  # 取前8位，足够唯一


@dataclass(frozen=True)
class LimitOrder:
    """
    限价单：指定价格买入/卖出

    使用场景：
    - 买入：在目标价位以下买入（例：昨收10元，限价10.10买入）
    - 卖出：在目标价位以上卖出（例：成本10元，限价11元卖出）

    成交规则：
    - 买入：当市场最低价 <= 限价时成交
    - 卖出：当市场最高价 >= 限价时成交

    示例：
        >>> order = LimitOrder(
        ...     symbol='000001.SZ',
        ...     direction='buy',
        ...     quantity=1000,
        ...     limit_price=10.50
        ... )
    """
    symbol: str           # 股票代码（如 '000001.SZ'）
    direction: str        # 方向：'buy' 或 'sell'
    quantity: int         # 数量（股）
    limit_price: float    # 限价（元）

    order_id: str = None                    # 订单ID（自动生成）
    submit_time: datetime = None            # 提交时间（自动生成）

    def __post_init__(self):
        """自动生成订单ID和提交时间"""
        if self.order_id is None:
            object.__setattr__(self, 'order_id', generate_order_id())
        if self.submit_time is None:
            object.__setattr__(self, 'submit_time', datetime.now())

        # 参数验证
        assert self.direction in ['buy', 'sell'], f"direction必须是'buy'或'sell'，收到：{self.direction}"
        assert self.quantity > 0, f"quantity必须>0，收到：{self.quantity}"
        assert self.quantity % 100 == 0, f"quantity必须是100的倍数（1手=100股），收到：{self.quantity}"
        assert self.limit_price > 0, f"limit_price必须>0，收到：{self.limit_price}"


@dataclass(frozen=True)
class StopOrder:
    """
    止损单：价格跌破触发价时卖出

    使用场景：
    - 风控：买入后设置止损，限制亏损（例：成本10元，触发价9.50 = -5%止损）

    成交规则：
    - 当市场最低价 <= 触发价时，触发止损
    - 触发后按"触发价 × (1 - 滑点)"成交（保守估计）

    重要提示：
    - Stage 1使用日线数据，无法精确模拟盘中触发时机
    - 保守估计：假设触发后价格继续下跌2%（滑点）

    示例：
        >>> order = StopOrder(
        ...     symbol='000001.SZ',
        ...     direction='sell',  # 止损通常是卖出
        ...     quantity=1000,
        ...     trigger_price=9.50  # 跌破9.50立即卖出
        ... )
    """
    symbol: str           # 股票代码
    direction: str        # 方向：通常是'sell'（止损卖出）
    quantity: int         # 数量（股）
    trigger_price: float  # 触发价（元）

    order_id: str = None                    # 订单ID（自动生成）
    submit_time: datetime = None            # 提交时间（自动生成）
    triggered: bool = False                 # 是否已触发

    def __post_init__(self):
        """自动生成订单ID和提交时间"""
        if self.order_id is None:
            object.__setattr__(self, 'order_id', generate_order_id())
        if self.submit_time is None:
            object.__setattr__(self, 'submit_time', datetime.now())

        # 参数验证
        assert self.direction in ['buy', 'sell'], f"direction必须是'buy'或'sell'，收到：{self.direction}"
        assert self.quantity > 0, f"quantity必须>0，收到：{self.quantity}"
        assert self.quantity % 100 == 0, f"quantity必须是100的倍数，收到：{self.quantity}"
        assert self.trigger_price > 0, f"trigger_price必须>0，收到：{self.trigger_price}"


@dataclass(frozen=True)
class Trade:
    """
    成交记录

    说明：
    - 委托单撮合成功后生成Trade对象
    - 用于记录实际成交价格、数量、时间

    示例：
        >>> trade = Trade(
        ...     order_id='abc123',
        ...     symbol='000001.SZ',
        ...     direction='buy',
        ...     fill_price=10.48,
        ...     fill_quantity=1000,
        ...     fill_time=datetime.now(),
        ...     commission=3.14
        ... )
    """
    order_id: str         # 关联的订单ID
    symbol: str           # 股票代码
    direction: str        # 方向：'buy' 或 'sell'
    fill_price: float     # 成交价（元）
    fill_quantity: int    # 成交数量（股）
    fill_time: datetime   # 成交时间
    commission: float     # 佣金（元）

    fill_type: str = 'limit'  # 成交类型：'limit', 'stop', 'market'

    def __post_init__(self):
        """参数验证"""
        assert self.direction in ['buy', 'sell'], f"direction必须是'buy'或'sell'，收到：{self.direction}"
        assert self.fill_price > 0, f"fill_price必须>0，收到：{self.fill_price}"
        assert self.fill_quantity > 0, f"fill_quantity必须>0，收到：{self.fill_quantity}"
        assert self.commission >= 0, f"commission必须>=0，收到：{self.commission}"

    @property
    def amount(self) -> float:
        """成交金额（不含佣金）"""
        return self.fill_price * self.fill_quantity

    @property
    def total_cost(self) -> float:
        """总成本（含佣金）"""
        return self.amount + self.commission


if __name__ == '__main__':
    # 简单测试
    print("=== 测试 LimitOrder ===")
    limit = LimitOrder(
        symbol='000001.SZ',
        direction='buy',
        quantity=1000,
        limit_price=10.50
    )
    print(f"订单ID: {limit.order_id}")
    print(f"提交时间: {limit.submit_time}")
    print(f"限价买入: {limit.symbol} {limit.quantity}股 @ ¥{limit.limit_price}")

    print("\n=== 测试 StopOrder ===")
    stop = StopOrder(
        symbol='000001.SZ',
        direction='sell',
        quantity=1000,
        trigger_price=9.50
    )
    print(f"订单ID: {stop.order_id}")
    print(f"止损卖出: {stop.symbol} {stop.quantity}股 @ 触发价¥{stop.trigger_price}")

    print("\n=== 测试 Trade ===")
    trade = Trade(
        order_id=limit.order_id,
        symbol='000001.SZ',
        direction='buy',
        fill_price=10.48,
        fill_quantity=1000,
        fill_time=datetime.now(),
        commission=3.14
    )
    print(f"成交: {trade.symbol} {trade.direction} {trade.fill_quantity}股 @ ¥{trade.fill_price}")
    print(f"成交金额: ¥{trade.amount:.2f}")
    print(f"总成本: ¥{trade.total_cost:.2f}（含佣金¥{trade.commission:.2f}）")
