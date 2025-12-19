"""
技术指标计算（KDJ, MA20）
"""
from __future__ import annotations

import pandas as pd
import numpy as np


def calculate_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """
    计算 KDJ 指标
    
    Args:
        df: DataFrame with columns: datetime, open, high, low, close, volume
        n: KDJ 周期
        m1: K 值平滑参数
        m2: D 值平滑参数
        
    Returns:
        DataFrame with added columns: K, D, J
    """
    df = df.copy()
    
    # 计算 RSV
    low_n = df['low'].rolling(n).min()
    high_n = df['high'].rolling(n).max()
    rsv = (df['close'] - low_n) / (high_n - low_n) * 100
    rsv = rsv.fillna(50)
    
    # 计算 K
    df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
    
    # 计算 D
    df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
    
    # 计算 J
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df


def calculate_ma(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    计算移动平均线
    
    Args:
        df: DataFrame
        period: MA 周期
        
    Returns:
        DataFrame with added column: MA{period}
    """
    df = df.copy()
    df[f'MA{period}'] = df['close'].rolling(period).mean()
    return df


def calculate_intraday_range(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算日内振幅 (K线内的振幅)
    
    Args:
        df: DataFrame with high, low, close
        
    Returns:
        DataFrame with added column: intraday_range
    """
    df = df.copy()
    df['intraday_range'] = (df['high'] - df['low']) / df['close']
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    添加所有需要的技术指标
    
    Args:
        df: 原始 K 线数据
        
    Returns:
        DataFrame with KDJ, MA20, intraday_range
    """
    if df.empty:
        return df
    
    df = calculate_kdj(df, n=9, m1=3, m2=3)
    df = calculate_ma(df, period=20)
    df = calculate_intraday_range(df)
    
    return df
