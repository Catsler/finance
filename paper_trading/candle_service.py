"""
K线数据服务 (用于图表展示)

提供60分钟K线数据，支持前复权/后复权/不复权。
遵循 bar_end_time 语义，过滤未完成K线。
"""
from __future__ import annotations

import logging
from datetime import datetime, time as dt_time
from typing import Literal

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)


def get_last_complete_60m_bar(now: datetime) -> datetime | None:
    """
    计算当前时刻最近一根"已完成"的60分钟K线的bar_end_time
    
    A股交易时段与60m bar_end_time对应关系:
    - 09:30-10:30 → 10:30
    - 10:30-11:30 → 11:30
    - 13:00-14:00 → 14:00
    - 14:00-15:00 → 15:00
    
    Args:
        now: 当前时间 (CN时区)
        
    Returns:
        最后一根已完成K线的bar_end_time，若交易未开始则返回 None
    """
    current_time = now.time()
    current_date = now.date()
    
    # 定义交易时段的60m bar结束时间点
    bar_ends = [
        dt_time(10, 30),  # 09:30-10:30
        dt_time(11, 30),  # 10:30-11:30
        dt_time(14, 0),   # 13:00-14:00  
        dt_time(15, 0),   # 14:00-15:00
    ]
    
    # 找到最后一根"已完成"(即 bar_end_time <= current_time)的K线
    last_complete = None
    for bar_end in bar_ends:
        if current_time >= bar_end:
            last_complete = datetime.combine(current_date, bar_end)
        else:
            break
    
    return last_complete


def fetch_60m_candles(
    symbol: str,
    adjust: Literal["front", "none", "back"] = "front",
    limit: int = 400,
) -> tuple[list[dict], datetime | None]:
    """
    获取60分钟K线数据
    
    Args:
        symbol: 股票代码 (如 000001.SZ)
        adjust: 复权类型 (front=前复权, none=不复权, back=后复权)
        limit: 返回最多的K线数量
        
    Returns:
        (candles, last_complete_time) 元组
        - candles: K线列表，每根K线包含 {time, open, high, low, close, volume}
        - last_complete_time: 最后一根已完成K线的bar_end_time
    """
    # 映射复权参数到AKShare格式
    adjust_map = {
        "front": "qfq",
        "none": "",
        "back": "hfq",
    }
    akshare_adjust = adjust_map.get(adjust, "")
    
    # 提取纯数字代码 (去掉 .SZ/.SH 后缀)
    code = symbol.replace('.SZ', '').replace('.SH', '')
    
    try:
        logger.info(f"Fetching 60m candles for {symbol}, adjust={adjust}, limit={limit}")
        
        # 调用 AKShare 获取60分钟K线 (period='60')
        df = ak.stock_zh_a_hist_min_em(
            symbol=code,
            period='60',
            adjust=akshare_adjust,
        )
        
        if df is None or df.empty:
            logger.warning(f"No data returned for {symbol}")
            return [], None
        
        # 重命名列 (AKShare返回中文列名)
        df = df.rename(columns={
            '时间': 'time',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
        })
        
        # 确保time列为datetime类型
        df['time'] = pd.to_datetime(df['time'])
        
        # 计算当前最后一根"已完成"K线的时间
        now = datetime.now()
        last_complete_time = get_last_complete_60m_bar(now)
        
        # 过滤未完成K线: 只保留 time <= last_complete_time
        if last_complete_time:
            df = df[df['time'] <= last_complete_time]
        
        # 按时间排序，取最近的limit根
        df = df.sort_values('time', ascending=False).head(limit)
        df = df.sort_values('time', ascending=True)  # 重新升序排列
        
        # 转换为字典列表
        candles = []
        for _, row in df.iterrows():
            candles.append({
                'time': row['time'].isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
            })
        
        logger.info(f"Fetched {len(candles)} candles, last_complete_time={last_complete_time}")
        return candles, last_complete_time
        
    except Exception as e:
        logger.error(f"Error fetching 60m candles for {symbol}: {e}")
        raise
