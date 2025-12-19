#!/usr/bin/env python3
"""
实时行情工具模块 - Phase 2

功能：
- 批量获取实时行情（带缓存）
- 手写缓存字典（vs lru_cache，逻辑更透明）
- 工具函数（清空缓存、统计信息）

用法：
    from utils.realtime_quote import get_realtime_quotes, clear_cache

    # 批量获取
    quotes = get_realtime_quotes(['600519.SH', '000001.SZ'])
    for q in quotes:
        print(f"{q['name']}: ¥{q['price']}")

    # 强制刷新
    clear_cache()
    quotes = get_realtime_quotes(['600519.SH'])

设计原则：
- 两层函数：底层(_fetch_sina_quote)可替换，上层(get_realtime_quotes)稳定
- 手写缓存：TTL精确控制，逻辑透明
- source字段：为多源扩展预留接口

新浪财经 API 字段定义：
    参考文档: https://blog.sina.com.cn/s/blog_5dc29fcc0101dq5s.html

    data 数组索引与单位（常用字段）:
        - data[0]: 股票名称
        - data[1]: 今开(元)
        - data[2]: 昨收(元)
        - data[3]: 现价(元)
        - data[4]: 最高(元)
        - data[5]: 最低(元)
        - data[6]: 买一价(元)
        - data[7]: 卖一价(元)
        - data[8]: 成交量(股) - 官方: "成交的股票数，使用时通常把该值除以一百"
        - data[9]: 成交额(元)
        - data[10]: 买一量(股)
        - data[20]: 卖一量(股)
        - data[30]: 日期(YYYY-MM-DD)
        - data[31]: 时间(HH:MM:SS)

    规范化处理:
        - volume: int(data[8]) // 100 → 转换为手（1手=100股）
        - amount: float(data[9]) / 10000 → 转换为万元（便于阅读）
        - price/open/high/low/prev_close: 保持元为单位

作者: Claude Code
日期: 2025-10-14
"""

import time
import random
import logging
from typing import List, Dict, Optional

try:
    import requests
except ImportError:
    raise ImportError("缺少依赖：pip3 install requests")

# 配置日志
logger = logging.getLogger(__name__)

# ===== 公开接口 =====
__all__ = [
    'fetch_sina_quote',      # 获取单只股票行情（公开接口）
    'get_realtime_quotes',   # 批量获取行情（公开接口）
    'clear_cache',           # 清空缓存（公开接口）
    'get_stats',             # 运行统计（公开接口）
    'reset_stats',           # 重置统计（测试用）
    'STANDARD_FIELDS',       # 字段单位说明（只读）
]

# ===== 缓存存储 =====

# NOTE: 当前实现为单用户环境设计（本地运行），无线程锁保护
#
# 多用户环境部署注意事项：
# 1. 缓存字典 _CACHE 和统计字典 _STATS 在并发访问时可能出现竞态条件
# 2. 表现：缓存命中计数不准确、clear_cache() 期间其他请求读到不一致状态
# 3. 解决方案（多用户部署时）：
#    _cache_lock = Lock()
#
#    # 在 get_realtime_quotes() 和 clear_cache() 中使用：
#    with _cache_lock:
#        # 缓存读写操作
#        ...
#
# 当前单用户环境无需加锁，保持 KISS 原则

_CACHE = {}  # {symbol: (quote_dict, expire_time)}
_STATS = {'success': 0, 'failure': 0, 'cache_hit': 0, 'cache_miss': 0}


# ===== 字段单位说明（详见模块 docstring） =====
# 新浪返回: data[8]=成交量(股), data[9]=成交额(元)
# 规范化: volume→手(÷100), amount→万元(÷10000), price系列→元(保持)

STANDARD_FIELDS = {
    'volume': '成交量(手)',
    'amount': '成交额(万元)',
    'price': '现价(元)',
    'open': '开盘(元)',
    'high': '最高(元)',
    'low': '最低(元)',
    'prev_close': '昨收(元)',
}


# ===== 底层：单次取报价（可替换数据源） =====

def _to_sina_code(symbol: str) -> str:
    """
    转换股票代码为新浪格式

    Args:
        symbol: 标准代码（如 '600519.SH', '000001.SZ'）

    Returns:
        新浪代码（如 'sh600519', 'sz000001'）

    Raises:
        ValueError: 代码格式无效
    """
    if '.SH' in symbol:
        return 'sh' + symbol.replace('.SH', '')
    elif '.SZ' in symbol:
        return 'sz' + symbol.replace('.SZ', '')
    else:
        raise ValueError(f"无效股票代码格式: {symbol}")


def _fetch_sina_quote(symbol: str) -> Optional[Dict]:
    """
    从新浪财经获取实时行情（带5层防御）

    Args:
        symbol: 标准股票代码

    Returns:
        行情字典，失败返回None
    """
    try:
        sina_code = _to_sina_code(symbol)
    except ValueError as e:
        logger.warning(f"代码转换失败: {e}")
        return None

    url = f"https://hq.sinajs.cn/list={sina_code}"
    headers = {'Referer': 'https://finance.sina.com.cn'}

    # 简单限速
    time.sleep(random.uniform(0.1, 0.3))

    try:
        response = requests.get(url, headers=headers, timeout=5)

        # 防御1：HTTP状态检查
        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code}: {symbol}")
            return None

        # 防御2：返回格式验证
        if '"' not in response.text:
            logger.warning(f"返回格式异常: {symbol}")
            return None

        raw_data = response.text.split('"')[1]

        # 防御3：空字符串判断（停牌/无效代码）
        if not raw_data or raw_data.strip() == '':
            logger.warning(f"数据为空（可能停牌）: {symbol}")
            return None

        data = raw_data.split(',')

        # 防御4：字段数量检查
        if len(data) < 32:
            logger.warning(f"字段不足: {symbol} (len={len(data)})")
            return None

        # 防御5：关键字段合理性检查
        try:
            name = data[0]
            price = float(data[3])
            prev_close = float(data[2])

            if price <= 0 or prev_close <= 0:
                logger.warning(f"价格异常: {symbol} (price={price}, prev_close={prev_close})")
                return None

        except (ValueError, IndexError) as e:
            logger.warning(f"字段解析失败: {symbol} - {e}")
            return None

        # 构造返回数据（单位规范化）
        #
        # NOTE:
        # - bid1/ask1/bid1_volume/ask1_volume 为盘口字段（若解析失败则为 None）
        # - 旧代码只依赖 price/prev_close 等字段，不会受新增字段影响
        bid1 = None
        ask1 = None
        bid1_volume = None
        ask1_volume = None
        try:
            bid1 = float(data[6]) if data[6] else None
            ask1 = float(data[7]) if data[7] else None
            bid1_volume = int(float(data[10])) if data[10] else None
            ask1_volume = int(float(data[20])) if data[20] else None
        except (ValueError, IndexError):
            bid1 = None
            ask1 = None
            bid1_volume = None
            ask1_volume = None

        return {
            'symbol': symbol,
            'name': name,
            'price': price,
            'bid1': bid1,
            'ask1': ask1,
            'bid1_volume': bid1_volume,
            'ask1_volume': ask1_volume,
            'prev_close': prev_close,
            'open': float(data[1]),
            'high': float(data[4]),
            'low': float(data[5]),
            'volume': int(data[8]) // 100,  # 转换为手（1手=100股）
            'amount': float(data[9]) / 10000,  # 转换为万元
            'change_pct': ((price / prev_close) - 1) * 100,
            'timestamp': f"{data[30]} {data[31]}",
            'source': 'sina',  # 数据来源标识
            'fetched_at': time.time()  # 获取时间戳
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"网络异常: {symbol} - {e}")
        return None
    except Exception as e:
        logger.error(f"未知异常: {symbol} - {e}")
        return None


def fetch_sina_quote(symbol: str) -> Optional[Dict]:
    """
    获取单只股票实时行情（公开接口）

    这是对外暴露的公开 API，内部调用 _fetch_sina_quote()。
    相比私有函数，此接口保证向后兼容性。

    Args:
        symbol: 标准股票代码（如 '600519.SH', '000001.SZ'）

    Returns:
        行情字典，失败返回None

    Example:
        >>> quote = fetch_sina_quote('600519.SH')
        >>> if quote:
        ...     print(f"{quote['name']}: ¥{quote['price']:.2f}")
        贵州茅台: ¥1451.27
    """
    return _fetch_sina_quote(symbol)


# ===== 上层：批量封装（对外接口） =====

def get_realtime_quotes(symbols: List[str], cache_seconds: int = 60) -> List[Dict]:
    """
    批量获取实时行情（带缓存）

    Args:
        symbols: 股票代码列表
        cache_seconds: 缓存时长（秒），默认60秒

    Returns:
        行情列表（失败的股票跳过）

    缓存逻辑：
        - 命中：直接返回缓存数据
        - 未命中/过期：调用_fetch_sina_quote并更新缓存

    Example:
        >>> quotes = get_realtime_quotes(['600519.SH', '000001.SZ'])
        >>> len(quotes)
        2
        >>> quotes[0]['name']
        '贵州茅台'
    """
    current_time = time.time()
    quotes = []

    for symbol in symbols:
        # 检查缓存
        if symbol in _CACHE:
            cached_quote, expire_time = _CACHE[symbol]
            if current_time < expire_time:
                # 缓存命中
                quotes.append(cached_quote)
                _STATS['cache_hit'] += 1
                continue

        # 缓存未命中或已过期
        _STATS['cache_miss'] += 1
        quote = _fetch_sina_quote(symbol)

        if quote:
            # 更新缓存
            _CACHE[symbol] = (quote, current_time + cache_seconds)
            quotes.append(quote)
            _STATS['success'] += 1
        else:
            _STATS['failure'] += 1

    return quotes


# ===== 工具函数 =====

def clear_cache():
    """
    清空缓存

    使用场景：
        - 用户点击"刷新"按钮强制更新
        - 测试时需要清理状态
    """
    _CACHE.clear()
    logger.info("缓存已清空")


def get_stats() -> Dict:
    """
    获取运行统计

    Returns:
        {
            'success': int,      # 成功次数
            'failure': int,      # 失败次数
            'cache_hit': int,    # 缓存命中次数
            'cache_miss': int,   # 缓存未命中次数
            'success_rate': str  # 成功率（百分比）
        }
    """
    total = _STATS['success'] + _STATS['failure']
    success_rate = (_STATS['success'] / total * 100) if total > 0 else 0

    return {
        **_STATS,
        'success_rate': f"{success_rate:.1f}%"
    }


def reset_stats():
    """重置统计数据（测试用）"""
    _STATS['success'] = 0
    _STATS['failure'] = 0
    _STATS['cache_hit'] = 0
    _STATS['cache_miss'] = 0


# ===== CLI测试入口 =====

if __name__ == '__main__':
    import sys

    logging.basicConfig(level=logging.INFO)

    # 调试函数：缓存统计（仅测试使用）
    def get_cache_stats() -> Dict:
        """
        获取缓存统计（调试用）

        Returns:
            {
                'total': int,      # 缓存总数
                'valid': int,      # 未过期数
                'expired': int,    # 已过期数
                'size_bytes': int  # 估算内存占用
            }
        """
        current_time = time.time()
        valid_count = 0
        expired_count = 0

        for _, expire_time in _CACHE.values():
            if current_time < expire_time:
                valid_count += 1
            else:
                expired_count += 1

        return {
            'total': len(_CACHE),
            'valid': valid_count,
            'expired': expired_count,
            'size_bytes': len(_CACHE) * 500  # 粗略估算：每条500字节
        }

    if len(sys.argv) < 2:
        print("用法：python utils/realtime_quote.py <股票代码1> [股票代码2] ...")
        print("示例：python utils/realtime_quote.py 600519.SH 000001.SZ")
        sys.exit(1)

    symbols = sys.argv[1:]

    print("=== 测试1: 首次获取（缓存未命中） ===")
    quotes1 = get_realtime_quotes(symbols)
    for q in quotes1:
        print(f"{q['name']}: ¥{q['price']:.2f} ({q['change_pct']:+.2f}%)")

    print(f"\n缓存统计: {get_cache_stats()}")
    print(f"运行统计: {get_stats()}")

    print("\n=== 测试2: 重复获取（缓存命中） ===")
    quotes2 = get_realtime_quotes(symbols)
    for q in quotes2:
        print(f"{q['name']}: ¥{q['price']:.2f} (fetched_at={q['fetched_at']:.0f})")

    print(f"\n缓存统计: {get_cache_stats()}")
    print(f"运行统计: {get_stats()}")

    print("\n=== 测试3: 清空缓存后重新获取 ===")
    clear_cache()
    quotes3 = get_realtime_quotes(symbols)
    print(f"获取数量: {len(quotes3)}")
    print(f"缓存统计: {get_cache_stats()}")
    print(f"运行统计: {get_stats()}")
