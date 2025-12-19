"""
Daily Trend Analysis Service

Provides daily trend classification (UP/DOWN/FLAT) based on MA20 slope and price position.
Uses qfq (front-adjusted) data to avoid false breakouts from dividends.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Literal

import pandas as pd

from utils.data_provider.akshare_provider import AKShareProvider

logger = logging.getLogger(__name__)

# Cache for daily trend results (symbol -> {trend, timestamp, data})
_trend_cache: dict[str, dict] = {}
_cache_ttl_seconds = 3600  # 1 hour TTL


def calculate_daily_trend(
    symbol: str,
    ma_period: int = 20,
    lookback: int = 5,
    eps_down: float = -0.008,  # -0.8%
    eps_up: float = 0.005,      # +0.5%
) -> dict:
    """
    Calculate daily trend classification
    
    Args:
        symbol: Stock symbol (e.g., "000001.SZ")
        ma_period: MA period (default 20)
        lookback: Lookback period for slope calculation (default 5)
        eps_down: Slope threshold for DOWN (default -0.8%)
        eps_up: Slope threshold for UP (default +0.5%)
    
    Returns:
        {
            'symbol': str,
            'trend': 'UP' | 'DOWN' | 'FLAT',
            'ma': int,
            'lookback': int,
            'adjust': 'qfq',
            'ma_last': float,
            'close_last': float,
            'slope': float,
            'asof_date': str,  # YYYY-MM-DD
            'close_time': str   # ISO timestamp
        }
    """
    # Check cache
    cache_key = f"{symbol}:{ma_period}:{lookback}"
    if cache_key in _trend_cache:
        cached = _trend_cache[cache_key]
        age = (datetime.now() - cached['timestamp']).total_seconds()
        if age < _cache_ttl_seconds:
            logger.info(f"Using cached trend for {symbol} (age: {age:.0f}s)")
            return cached['data']
    
    try:
        # Fetch daily data (qfq, last 60-120 days is enough)
        provider = AKShareProvider()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching daily data for {symbol} (qfq, {start_date} to {end_date})")
        
        daily_df = provider.get_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )
        
        if daily_df is None or len(daily_df) < ma_period + lookback:
            raise ValueError(f"Insufficient data for {symbol}: got {len(daily_df) if daily_df is not None else 0} rows")
        
        # Calculate MA20
        daily_df['ma'] = daily_df['close'].rolling(ma_period).mean()
        
        # Get latest values
        ma_last = daily_df['ma'].iloc[-1]
        close_last = daily_df['close'].iloc[-1]
        asof_date = daily_df['date'].iloc[-1]
        
        # Calculate slope over lookback period
        ma_lookback = daily_df['ma'].iloc[-lookback - 1]  # -lookback-1 because we want lookback days ago
        slope = (ma_last - ma_lookback) / ma_lookback
        
        # Determine trend with二次确认 rule
        if slope < eps_down and close_last < ma_last:
            trend = 'DOWN'
        elif slope > eps_up and close_last > ma_last:
            trend = 'UP'
        else:
            trend = 'FLAT'
        
        # Construct close_time (assume 15:00 for daily close)
        if isinstance(asof_date, str):
            close_time = f"{asof_date}T15:00:00"
        else:
            close_time = asof_date.strftime('%Y-%m-%dT15:00:00')
        
        result = {
            'symbol': symbol,
            'trend': trend,
            'ma': ma_period,
            'lookback': lookback,
            'adjust': 'qfq',
            'ma_last': float(ma_last),
            'close_last': float(close_last),
            'slope': float(slope),
            'asof_date': asof_date.strftime('%Y-%m-%d') if hasattr(asof_date, 'strftime') else asof_date,
            'close_time': close_time
        }
        
        # Cache result
        _trend_cache[cache_key] = {
            'data': result,
            'timestamp': datetime.now()
        }
        
        logger.info(f"{symbol} trend: {trend} (slope={slope:.4f}, close={close_last:.2f}, ma={ma_last:.2f})")
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating daily trend for {symbol}: {e}")
        raise


def clear_trend_cache(symbol: str | None = None):
    """Clear cache for a specific symbol or all symbols"""
    global _trend_cache
    if symbol:
        _trend_cache = {k: v for k, v in _trend_cache.items() if not k.startswith(symbol + ':')}
    else:
        _trend_cache = {}
