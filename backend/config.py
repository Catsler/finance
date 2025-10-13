#!/usr/bin/env python3
"""
统一配置文件 - HS300智能选股系统

功能：
1. 路径配置：统一data/目录管理
2. 系统参数：预算、候选数等默认值
3. 缓存配置：成分股缓存有效期
"""

from pathlib import Path
from datetime import datetime

# ===== 项目根目录 =====
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# ===== 数据目录（统一管理） =====
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DAILY_DIR = DATA_DIR / "daily"
PORTFOLIO_DIR = DATA_DIR / "portfolio"

# ===== 外部依赖目录 =====
QLIB_DATA_DIR = Path.home() / ".qlib/qlib_data/cn_data"

# ===== 历史目录（向后兼容） =====
RESULTS_DIR = PROJECT_ROOT / "results"

# ===== 自动创建目录 =====
for directory in [CACHE_DIR, DAILY_DIR, PORTFOLIO_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ===== 文件路径配置 =====
# 缓存文件
HS300_CACHE_FILE = CACHE_DIR / "hs300_constituents.json"
STOCK_METADATA_CACHE = CACHE_DIR / "stock_metadata.json"

# 虚拟持仓
VIRTUAL_PORTFOLIO_FILE = PORTFOLIO_DIR / "virtual.json"
TRADES_LOG_FILE = PORTFOLIO_DIR / "trades.jsonl"

# ===== 系统参数 =====
# 预算配置
DEFAULT_BUDGET = 100000  # 默认10万元
MIN_REQUIRED_BUDGET = 20000  # 最低门槛

# 选股参数
DEFAULT_TOP_N = 5  # 默认候选数
DEFAULT_MOMENTUM_THRESHOLD = 0.0  # 默认涨幅阈值

# 缓存配置
HS300_CACHE_DAYS = 7  # 成分股缓存有效期（天）

# ===== 工具函数 =====
def get_daily_path(date=None):
    """
    获取指定日期的播报目录

    Args:
        date: datetime对象或字符串(YYYY-MM-DD)，默认当日

    Returns:
        Path: data/daily/YYYY-MM-DD/
    """
    if date is None:
        date = datetime.now()
    elif isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')

    date_str = date.strftime('%Y-%m-%d')
    daily_path = DAILY_DIR / date_str
    daily_path.mkdir(parents=True, exist_ok=True)

    return daily_path

def get_selection_file(date=None):
    """获取选股结果JSON路径"""
    return get_daily_path(date) / "selection.json"

def get_report_file(date=None):
    """获取Markdown报告路径"""
    return get_daily_path(date) / "report.md"

def get_latest_selection():
    """获取最新选股结果路径"""
    latest_link = DAILY_DIR / "latest.json"
    if latest_link.exists() and latest_link.is_symlink():
        return latest_link
    return None

def create_latest_link(date=None):
    """创建latest.json软链接指向最新结果"""
    latest_link = DAILY_DIR / "latest.json"
    target = get_selection_file(date)

    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()

    # 创建相对路径软链接
    relative_target = target.relative_to(DAILY_DIR)
    latest_link.symlink_to(relative_target)

    return latest_link
