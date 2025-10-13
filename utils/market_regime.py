"""
市场状态识别模块

功能:
    根据HS300指数的动量和波动率识别市场状态

状态分类:
    - bull (牛市): 20日涨幅>5% AND 波动率<15%
    - bear (熊市): 20日涨幅<-5%
    - sideways (震荡): 其他情况

使用:
    from utils.market_regime import identify_market_regime

    regime = identify_market_regime(hs300_data, date)
    # 返回: 'bull', 'bear', 或 'sideways'
"""

import pandas as pd
import numpy as np


def identify_market_regime(
    hs300_data,
    date,
    momentum_bull_threshold=0.05,
    momentum_bear_threshold=-0.05,
    volatility_threshold=0.15
):
    """
    识别指定日期的市场状态

    Args:
        hs300_data: HS300数据DataFrame（包含date和close列）
        date: 要识别的日期（pd.Timestamp或字符串）
        momentum_bull_threshold: 牛市动量阈值（默认5%）
        momentum_bear_threshold: 熊市动量阈值（默认-5%）
        volatility_threshold: 牛市波动率阈值（默认15%）

    Returns:
        str: 'bull', 'bear', 或 'sideways'
    """
    # 转换日期格式
    if isinstance(date, str):
        date = pd.Timestamp(date)

    # 确保数据有索引
    if not isinstance(hs300_data.index, pd.DatetimeIndex):
        hs300_data = hs300_data.copy()
        hs300_data['date'] = pd.to_datetime(hs300_data['date'])
        hs300_data = hs300_data.set_index('date')

    # 检查日期是否在数据范围内
    if date not in hs300_data.index:
        # 如果精确日期不存在，找最近的交易日
        if date < hs300_data.index[0]:
            return 'sideways'  # 默认返回震荡
        if date > hs300_data.index[-1]:
            date = hs300_data.index[-1]
        else:
            # 找前一个交易日
            date = hs300_data.index[hs300_data.index <= date][-1]

    # 获取日期位置
    date_loc = hs300_data.index.get_loc(date)

    # 需要至少20个交易日数据
    if date_loc < 20:
        return 'sideways'  # 数据不足，默认震荡

    # 计算20日动量
    close_today = hs300_data.iloc[date_loc]['close']
    close_20d_ago = hs300_data.iloc[date_loc - 20]['close']
    momentum_20d = (close_today - close_20d_ago) / close_20d_ago

    # 计算20日波动率（年化）
    daily_returns = hs300_data.iloc[date_loc - 19:date_loc + 1]['close'].pct_change()
    volatility = daily_returns.std() * np.sqrt(252)  # 年化波动率

    # 市场状态判断
    if momentum_20d > momentum_bull_threshold and volatility < volatility_threshold:
        return 'bull'
    elif momentum_20d < momentum_bear_threshold:
        return 'bear'
    else:
        return 'sideways'


def identify_regime_for_dates(hs300_data, dates, **kwargs):
    """
    批量识别多个日期的市场状态

    Args:
        hs300_data: HS300数据DataFrame
        dates: 日期列表
        **kwargs: 传递给identify_market_regime的参数

    Returns:
        dict: {date: regime}
    """
    regimes = {}

    for date in dates:
        regime = identify_market_regime(hs300_data, date, **kwargs)
        regimes[date if isinstance(date, str) else date.strftime('%Y-%m-%d')] = regime

    return regimes


def get_regime_statistics(regimes):
    """
    统计市场状态分布

    Args:
        regimes: {date: regime} 字典

    Returns:
        dict: 统计信息
    """
    from collections import Counter

    regime_counts = Counter(regimes.values())
    total = len(regimes)

    return {
        'total_periods': total,
        'bull_count': regime_counts.get('bull', 0),
        'bear_count': regime_counts.get('bear', 0),
        'sideways_count': regime_counts.get('sideways', 0),
        'bull_pct': regime_counts.get('bull', 0) / total * 100 if total > 0 else 0,
        'bear_pct': regime_counts.get('bear', 0) / total * 100 if total > 0 else 0,
        'sideways_pct': regime_counts.get('sideways', 0) / total * 100 if total > 0 else 0
    }
