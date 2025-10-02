"""
IO工具函数：目录管理、缓存、JSON序列化、版本追踪
"""

import os
import json
import subprocess
from datetime import datetime
import pandas as pd


def ensure_directories():
    """
    确保所有必需的目录存在
    """
    dirs = ['results', 'scripts', 'notebooks', 'utils']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 扩展用户目录
    data_dir = os.path.expanduser('~/.qlib/qlib_data/cn_data')
    os.makedirs(data_dir, exist_ok=True)

    print("✓ 目录结构已确认")


def get_git_info():
    """
    获取当前git信息（commit hash + branch + dirty状态）

    Returns:
        dict: {'commit': 'abc123', 'branch': 'main', 'dirty': False}
        如果不是git仓库，返回None
    """
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # 检查是否有未提交的修改
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        dirty = len(status) > 0

        return {
            'commit': commit[:8],  # 短hash
            'branch': branch,
            'dirty': dirty
        }
    except:
        return None


def save_json_with_metadata(data, filepath, phase=None, version='1.0.0'):
    """
    保存JSON并自动添加元数据（timestamp, version, git信息）

    Args:
        data: 要保存的数据（dict）
        filepath: 输出文件路径
        phase: Phase名称（如'Phase 6D'）
        version: 语义版本号
    """
    # 添加元数据
    output = {
        **data,  # 原始数据
        '_metadata': {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'phase': phase,
            'version': version,
            'git': get_git_info()
        }
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ 已保存: {filepath}")
    if output['_metadata']['git']:
        git_info = output['_metadata']['git']
        status = ' (有未提交修改)' if git_info['dirty'] else ''
        print(f"  Git: {git_info['commit']} @ {git_info['branch']}{status}")


def load_json(filepath):
    """
    加载JSON文件

    Returns:
        data: 原始数据（不含_metadata）
        metadata: 元数据（如果存在）
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        full_data = json.load(f)

    metadata = full_data.pop('_metadata', None)
    return full_data, metadata


def load_benchmark_data(start_date='2021-01-01', end_date='2025-09-30'):
    """
    下载沪深300指数数据并缓存到本地，记录完整元数据

    Args:
        start_date: 起始日期（默认2021-01-01，支持Phase 8回归测试）
        end_date: 结束日期（默认2025-09-30，覆盖Phase 7数据）

    Returns:
        DataFrame: 沪深300指数数据
    """
    cache_file = 'results/benchmark_hs300.csv'
    meta_file = 'results/benchmark_hs300_meta.json'

    # 检查缓存
    if os.path.exists(cache_file) and os.path.exists(meta_file):
        with open(meta_file, 'r') as f:
            meta = json.load(f)

        df = pd.read_csv(cache_file, parse_dates=['date'])

        # 验证时间范围
        cached_start = pd.to_datetime(meta['start_date'])
        cached_end = pd.to_datetime(meta['end_date'])
        required_start = pd.to_datetime(start_date)
        required_end = pd.to_datetime(end_date)

        if cached_start <= required_start and cached_end >= required_end:
            print(f"✓ 从缓存加载沪深300数据")
            print(f"  缓存时间: {meta['last_updated']}")
            print(f"  覆盖范围: {meta['start_date']} ~ {meta['end_date']}")
            return df
        else:
            print(f"⚠️ 缓存范围不足")
            print(f"  需要: {start_date} ~ {end_date}")
            print(f"  缓存: {meta['start_date']} ~ {meta['end_date']}")
            print(f"  重新下载...")

    # 下载数据
    print("下载沪深300指数数据...")
    import akshare as ak
    df = ak.stock_zh_index_daily(symbol="sh000300")

    # 确保date列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])

    # 使用参数化起始日期过滤（支持2021-2025，Phase 8扩展）
    df = df[df['date'] >= pd.Timestamp(start_date)]

    # 缓存数据
    df.to_csv(cache_file, index=False)

    # 保存元数据
    meta = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'start_date': df['date'].min().strftime('%Y-%m-%d'),
        'end_date': df['date'].max().strftime('%Y-%m-%d'),
        'data_points': len(df),
        'source': 'akshare.stock_zh_index_daily',
        'symbol': 'sh000300'
    }

    with open(meta_file, 'w') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"✓ 沪深300数据已缓存: {cache_file}")
    print(f"  时间范围: {meta['start_date']} ~ {meta['end_date']}")
    print(f"  数据点数: {meta['data_points']}")

    return df
