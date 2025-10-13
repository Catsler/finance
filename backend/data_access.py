#!/usr/bin/env python3
"""
数据访问层 - Data Access Layer

功能：
1. 每日选股数据读取
2. 历史记录查询
3. 持仓数据访问
4. 数据缓存管理

使用示例：
    from backend.data_access import DataAccess

    data = DataAccess()
    latest = data.get_latest_selection()
    history = data.get_selection_history(days=7)
    portfolio = data.get_portfolio_stats()
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from backend.config import (
    DAILY_DIR,
    VIRTUAL_PORTFOLIO_FILE,
    TRADES_LOG_FILE,
    get_selection_file,
    get_latest_selection
)
from backend.portfolio_manager import VirtualPortfolio


class DataAccess:
    """数据访问统一接口"""

    def __init__(self):
        """初始化数据访问层"""
        self.portfolio = None  # 延迟加载

    # ===== 选股数据访问 =====

    def get_latest_selection(self) -> Optional[Dict]:
        """
        获取最新选股结果

        Returns:
            dict: 选股结果，如果不存在返回None
        """
        latest_link = get_latest_selection()

        if latest_link and latest_link.exists():
            try:
                with open(latest_link, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # 备用：查找最新日期目录
        return self._get_most_recent_selection()

    def _get_most_recent_selection(self) -> Optional[Dict]:
        """获取最近日期的选股结果"""
        if not DAILY_DIR.exists():
            return None

        # 查找所有日期目录
        date_dirs = [d for d in DAILY_DIR.iterdir() if d.is_dir() and d.name.count('-') == 2]

        if not date_dirs:
            return None

        # 按日期排序，取最新
        date_dirs.sort(reverse=True)
        latest_dir = date_dirs[0]

        selection_file = latest_dir / "selection.json"
        if selection_file.exists():
            try:
                with open(selection_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        return None

    def get_selection_by_date(self, date: str) -> Optional[Dict]:
        """
        获取指定日期的选股结果

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            dict: 选股结果，如果不存在返回None
        """
        selection_file = get_selection_file(date)

        if selection_file.exists():
            try:
                with open(selection_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        return None

    def get_selection_history(self, days: int = 7) -> List[Dict]:
        """
        获取历史选股记录

        Args:
            days: 返回最近N天的记录

        Returns:
            list: 选股结果列表，按日期倒序
        """
        if not DAILY_DIR.exists():
            return []

        # 查找所有日期目录
        date_dirs = [d for d in DAILY_DIR.iterdir() if d.is_dir() and d.name.count('-') == 2]

        if not date_dirs:
            return []

        # 按日期排序（倒序）
        date_dirs.sort(reverse=True)

        # 读取前N个
        history = []
        for date_dir in date_dirs[:days]:
            selection_file = date_dir / "selection.json"
            if selection_file.exists():
                try:
                    with open(selection_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history.append(data)
                except Exception:
                    continue

        return history

    def get_available_dates(self) -> List[str]:
        """
        获取所有可用的选股日期

        Returns:
            list: 日期列表 (YYYY-MM-DD)，按倒序排列
        """
        if not DAILY_DIR.exists():
            return []

        date_dirs = [d.name for d in DAILY_DIR.iterdir() if d.is_dir() and d.name.count('-') == 2]
        date_dirs.sort(reverse=True)

        return date_dirs

    # ===== 持仓数据访问 =====

    def get_portfolio_stats(self, date: Optional[str] = None) -> Dict:
        """
        获取持仓统计

        Args:
            date: 统计日期，默认最新

        Returns:
            dict: 持仓统计信息
        """
        if self.portfolio is None:
            self.portfolio = VirtualPortfolio(load_existing=True)

        return self.portfolio.get_stats(date)

    def get_portfolio_positions(self, date: Optional[str] = None) -> List[Dict]:
        """
        获取持仓明细

        Args:
            date: 统计日期

        Returns:
            list: 持仓列表
        """
        stats = self.get_portfolio_stats(date)
        return stats.get('positions', [])

    def get_trade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        获取交易历史

        Args:
            limit: 返回最近N条记录

        Returns:
            list: 交易记录列表
        """
        if self.portfolio is None:
            self.portfolio = VirtualPortfolio(load_existing=True)

        return self.portfolio.get_trade_history(limit)

    def has_portfolio(self) -> bool:
        """
        检查是否存在持仓数据

        Returns:
            bool: 是否存在持仓
        """
        return VIRTUAL_PORTFOLIO_FILE.exists()

    # ===== 数据对比分析 =====

    def compare_selections(self, date1: str, date2: str) -> Dict:
        """
        对比两个日期的选股结果

        Args:
            date1: 第一个日期
            date2: 第二个日期

        Returns:
            dict: {
                'date1': str,
                'date2': str,
                'new': set,  # 新增候选
                'removed': set,  # 移除候选
                'continued': set,  # 持续候选
                'selection1': dict,
                'selection2': dict
            }
        """
        selection1 = self.get_selection_by_date(date1)
        selection2 = self.get_selection_by_date(date2)

        if not selection1 or not selection2:
            return {
                'error': '数据不完整',
                'date1': date1,
                'date2': date2
            }

        # 提取候选股票集合
        symbols1 = {s['symbol'] for s in selection1.get('selected', [])}
        symbols2 = {s['symbol'] for s in selection2.get('selected', [])}

        return {
            'date1': date1,
            'date2': date2,
            'new': symbols2 - symbols1,
            'removed': symbols1 - symbols2,
            'continued': symbols1 & symbols2,
            'selection1': selection1,
            'selection2': selection2
        }

    def get_performance_summary(self, days: int = 30) -> Dict:
        """
        获取收益概览（基于交易历史）

        Args:
            days: 统计最近N天

        Returns:
            dict: {
                'total_trades': int,
                'buy_count': int,
                'sell_count': int,
                'realized_pnl': float,
                'win_rate': float,
                'trades': List[Dict]
            }
        """
        trades = self.get_trade_history()

        if not trades:
            return {
                'total_trades': 0,
                'buy_count': 0,
                'sell_count': 0,
                'realized_pnl': 0.0,
                'win_rate': 0.0,
                'trades': []
            }

        # 过滤最近N天的交易
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        recent_trades = [t for t in trades if t.get('date', '') >= cutoff_date]

        # 统计
        buy_count = sum(1 for t in recent_trades if t['type'] == 'buy')
        sell_count = sum(1 for t in recent_trades if t['type'] == 'sell')
        realized_pnl = sum(t.get('profit', 0) for t in recent_trades if t['type'] == 'sell')

        # 胜率（盈利交易占比）
        sell_trades = [t for t in recent_trades if t['type'] == 'sell']
        win_count = sum(1 for t in sell_trades if t.get('profit', 0) > 0)
        win_rate = (win_count / len(sell_trades) * 100) if sell_trades else 0

        return {
            'total_trades': len(recent_trades),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'realized_pnl': realized_pnl,
            'win_rate': win_rate,
            'trades': recent_trades
        }

    # ===== 统计辅助函数 =====

    def get_summary_stats(self) -> Dict:
        """
        获取系统整体统计

        Returns:
            dict: {
                'total_selections': int,
                'latest_selection_date': str,
                'has_portfolio': bool,
                'portfolio_value': float,
                'total_trades': int
            }
        """
        available_dates = self.get_available_dates()

        stats = {
            'total_selections': len(available_dates),
            'latest_selection_date': available_dates[0] if available_dates else None,
            'has_portfolio': self.has_portfolio(),
            'portfolio_value': 0.0,
            'total_trades': 0
        }

        if stats['has_portfolio']:
            portfolio_stats = self.get_portfolio_stats()
            stats['portfolio_value'] = portfolio_stats.get('total_value', 0)

            trades = self.get_trade_history()
            stats['total_trades'] = len(trades)

        return stats


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 data_access.py...\n")

    data = DataAccess()

    # 测试1: 获取最新选股
    print("测试1: 获取最新选股")
    latest = data.get_latest_selection()
    if latest:
        print(f"✓ 最新日期: {latest['metadata']['date']}")
        print(f"✓ 候选数: {len(latest['selected'])}")
    else:
        print("⚠️ 暂无选股数据")

    # 测试2: 历史记录
    print("\n测试2: 历史记录")
    history = data.get_selection_history(days=7)
    print(f"✓ 最近7天记录数: {len(history)}")

    # 测试3: 可用日期
    print("\n测试3: 可用日期")
    dates = data.get_available_dates()
    print(f"✓ 可用日期数: {len(dates)}")
    if dates:
        print(f"✓ 最新: {dates[0]}")

    # 测试4: 持仓统计
    print("\n测试4: 持仓统计")
    if data.has_portfolio():
        stats = data.get_portfolio_stats()
        print(f"✓ 总市值: {stats['total_value']:.0f} 元")
        print(f"✓ 持仓数: {len(stats['positions'])}")
    else:
        print("⚠️ 暂无持仓数据")

    # 测试5: 系统摘要
    print("\n测试5: 系统摘要")
    summary = data.get_summary_stats()
    print(f"✓ 总选股次数: {summary['total_selections']}")
    print(f"✓ 持仓存在: {summary['has_portfolio']}")
    print(f"✓ 总交易数: {summary['total_trades']}")

    print("\n✅ 测试完成")
