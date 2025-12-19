"""
60分钟 K 线数据获取与管理
"""
from __future__ import annotations

import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def fetch_60m_kline(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    获取指定股票的 60 分钟 K 线数据
    
    Args:
        symbol: 股票代码，如 "000001.SZ"
        days: 获取最近多少天的数据
        
    Returns:
        DataFrame with columns: datetime, open, high, low, close, volume
    """
    # 转换为 AKShare 格式
    code = symbol.split('.')[0]
    
    try:
        # AKShare 分钟数据接口
        df = ak.stock_zh_a_hist_min_em(
            symbol=code,
            period='60',  # 60分钟
            adjust=''     # 不复权（实时交易用真实价格）
        )
        
        if df.empty:
            return pd.DataFrame()
        
        # 重命名列
        df.columns = ['datetime', 'open', 'close', 'high', 'low', 'volume', 'money', 'latest']
        
        # 只保留需要的列
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        # 转换时间
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 过滤最近 N 天
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['datetime'] >= cutoff].copy()
        
        # 按时间排序
        df = df.sort_values('datetime').reset_index(drop=True)
        
        return df
        
    except Exception as e:
        print(f"获取 {symbol} 60分钟数据失败: {e}")
        return pd.DataFrame()


def save_60m_cache(symbol: str, df: pd.DataFrame, cache_dir: Path = Path('data/cache_60m')):
    """保存 60 分钟数据到缓存"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f'{symbol}.csv'
    df.to_csv(cache_file, index=False)


def load_60m_cache(symbol: str, max_age_hours: int = 1, cache_dir: Path = Path('data/cache_60m')) -> Optional[pd.DataFrame]:
    """
    从缓存加载 60 分钟数据
    
    Args:
        symbol: 股票代码
        max_age_hours: 缓存最大有效时长（小时）
        
    Returns:
        DataFrame or None
    """
    cache_file = cache_dir / f'{symbol}.csv'
    
    if not cache_file.exists():
        return None
    
    # 检查缓存时效
    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
    if datetime.now() - file_time > timedelta(hours=max_age_hours):
        return None
    
    try:
        df = pd.read_csv(cache_file)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    except Exception:
        return None


def get_60m_kline(symbol: str, use_cache: bool = True) -> pd.DataFrame:
    """
    获取 60 分钟数据（优先使用缓存）
    
    Args:
        symbol: 股票代码
        use_cache: 是否使用缓存
        
    Returns:
        DataFrame
    """
    # 尝试缓存
    if use_cache:
        df = load_60m_cache(symbol)
        if df is not None and not df.empty:
            return df
    
    # 重新获取
    df = fetch_60m_kline(symbol)
    
    # 保存缓存
    if not df.empty:
        save_60m_cache(symbol, df)
    
    return df
