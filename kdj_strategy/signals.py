"""
KDJ 信号生成逻辑
"""
from __future__ import annotations

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Literal
from dataclasses import dataclass


@dataclass
class Signal:
    """交易信号"""
    symbol: str
    direction: Literal['BUY', 'SELL']
    quantity: int
    signal_type: Literal['LOW_BUY', 'HIGH_SELL']
    signal_time: datetime
    reason: str
    
    # 指标快照
    J: float
    K: float
    D: float
    close: float
    MA20: float
    intraday_range: float


class SignalGenerator:
    """KDJ 信号生成器"""
    
    def __init__(
        self,
        buy_threshold: float = 25,
        sell_threshold: float = 75,
        min_range: float = 0.02,
        quantity: int = 400,
    ):
        """
        Args:
            buy_threshold: 买入 J 阈值
            sell_threshold: 卖出 J 阈值
            min_range: 最小振幅要求
            quantity: 每次交易股数
        """
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.min_range = min_range
        self.quantity = quantity
    
    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Optional[Signal]:
        """
        基于最新 K 线生成信号
        
        Args:
            symbol: 股票代码
            df: 包含 KDJ, MA20, intraday_range 的 DataFrame
            
        Returns:
            Signal or None
        """
        if df.empty or len(df) < 20:
            return None
        
        # 获取最新一根 K 线
        latest = df.iloc[-1]
        
        # 检查必要字段
        required_fields = ['J', 'K', 'D', 'close', 'MA20', 'intraday_range', 'datetime']
        if not all(field in latest.index for field in required_fields):
            return None
        
        # 提取指标
        J = latest['J']
        close = latest['close']
        MA20 = latest['MA20']
        intraday_range = latest['intraday_range']
        signal_time = pd.to_datetime(latest['datetime'])
        
        # 跳过 NaN
        if pd.isna(J) or pd.isna(MA20) or pd.isna(intraday_range):
            return None
        
        # 振幅过滤
        if intraday_range < self.min_range:
            return None
        
        # 买入信号：J < 25 且 close < MA20
        if J < self.buy_threshold and close < MA20:
            return Signal(
                symbol=symbol,
                direction='BUY',
                quantity=self.quantity,
                signal_type='LOW_BUY',
                signal_time=signal_time,
                reason=f'J={J:.1f}<{self.buy_threshold}, close<MA20, range={intraday_range*100:.1f}%',
                J=float(J),
                K=float(latest['K']),
                D=float(latest['D']),
                close=float(close),
                MA20=float(MA20),
                intraday_range=float(intraday_range),
            )
        
        # 卖出信号：J > 75 且 close > MA20
        if J > self.sell_threshold and close > MA20:
            return Signal(
                symbol=symbol,
                direction='SELL',
                quantity=self.quantity,
                signal_type='HIGH_SELL',
                signal_time=signal_time,
                reason=f'J={J:.1f}>{self.sell_threshold}, close>MA20, range={intraday_range*100:.1f}%',
                J=float(J),
                K=float(latest['K']),
                D=float(latest['D']),
                close=float(close),
                MA20=float(MA20),
                intraday_range=float(intraday_range),
            )
        
        return None
