"""
分时数据服务

提供分钟级K线数据的获取和缓存功能。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from utils.data_provider.akshare_provider import AKShareProvider


class IntradayService:
    """分时数据服务
    
    负责获取当日分钟级K线数据，并计算均价（VWAP）。
    """
    
    def __init__(self):
        self.provider = AKShareProvider()
        self._cache = {}  # Simple in-memory cache: {symbol: {data, timestamp}}
        self._cache_ttl = 60  # Cache TTL in seconds
    
    def get_intraday(self, symbol: str, period: str = '1') -> dict[str, Any]:
        """
        获取分时数据
        
        Args:
            symbol: 股票代码 (如: 002812.SZ)
            period: 数据周期 ('1', '5', '15', '30', '60')
        
        Returns:
            {
                'symbol': str,
                'date': str (YYYY-MM-DD),
                'bars': List[dict],  # [{time, open, high, low, close, volume, amount}, ...]
                'avg_price': float   # VWAP (Volume-Weighted Average Price)
            }
        """
        # Check cache
        cache_key = f"{symbol}_{period}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.now() - cached['timestamp']).total_seconds()
            if age < self._cache_ttl:
                return cached['data']
        
        # Fetch from provider
        try:
            df = self.provider.get_intraday_data(symbol, period)
            
            if df.empty:
                return {
                    'symbol': symbol,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'bars': [],
                    'avg_price': 0.0
                }
            
            # Convert to list of dicts
            bars = df.to_dict('records')
            
            # Calculate VWAP (Volume-Weighted Average Price)
            total_value = (df['close'] * df['volume']).sum()
            total_volume = df['volume'].sum()
            avg_price = total_value / total_volume if total_volume > 0 else df['close'].mean()
            
            result = {
                'symbol': symbol,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'bars': bars,
                'avg_price': float(avg_price)
            }
            
            # Update cache
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            # Return empty result on error
            return {
                'symbol': symbol,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'bars': [],
                'avg_price': 0.0,
                'error': str(e)
            }
