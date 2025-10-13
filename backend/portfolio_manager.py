#!/usr/bin/env python3
"""
虚拟持仓管理 - Portfolio Manager

功能：
1. 持仓管理 - 买入/卖出/持仓状态跟踪
2. 月度再平衡 - 模拟Phase 6D逻辑
3. 收益计算 - 日度/累计收益率
4. 交易日志 - JSONL格式记录所有交易
5. 状态持久化 - JSON格式保存持仓状态

使用示例：
    from backend.portfolio_manager import VirtualPortfolio

    portfolio = VirtualPortfolio(initial_cash=100000)
    portfolio.rebalance(selected_stocks, date='2025-01-15')
    portfolio.update_prices(date='2025-01-16')
    stats = portfolio.get_stats()
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

from backend.config import (
    VIRTUAL_PORTFOLIO_FILE,
    TRADES_LOG_FILE,
    QLIB_DATA_DIR
)


class VirtualPortfolio:
    """虚拟持仓管理器"""

    def __init__(self, initial_cash: float = 100000, load_existing: bool = True):
        """
        初始化虚拟持仓

        Args:
            initial_cash: 初始资金（元）
            load_existing: 是否加载现有持仓
        """
        self.initial_cash = initial_cash

        if load_existing and VIRTUAL_PORTFOLIO_FILE.exists():
            self._load_state()
        else:
            self._initialize_state(initial_cash)

    def _initialize_state(self, cash: float):
        """初始化空持仓"""
        self.cash = cash
        self.holdings = {}  # {symbol: {'shares': int, 'cost_basis': float, 'name': str}}
        self.created_at = datetime.now().isoformat()
        self.last_rebalance_date = None
        self.trades_count = 0

    def _load_state(self):
        """从JSON加载持仓状态"""
        with open(VIRTUAL_PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)

        self.cash = state['cash']
        self.holdings = state['holdings']
        self.created_at = state['created_at']
        self.last_rebalance_date = state.get('last_rebalance_date')
        self.trades_count = state.get('trades_count', 0)

    def _save_state(self):
        """保存持仓状态到JSON"""
        state = {
            'cash': self.cash,
            'holdings': self.holdings,
            'created_at': self.created_at,
            'last_rebalance_date': self.last_rebalance_date,
            'trades_count': self.trades_count,
            'updated_at': datetime.now().isoformat()
        }

        VIRTUAL_PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(VIRTUAL_PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _log_trade(self, trade: Dict):
        """记录交易到JSONL日志"""
        trade['timestamp'] = datetime.now().isoformat()
        trade['trade_id'] = self.trades_count

        TRADES_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRADES_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trade, ensure_ascii=False) + '\n')

        self.trades_count += 1

    def _get_current_price(self, symbol: str, date: Optional[str] = None) -> Optional[float]:
        """
        获取股票当前价格（从Qlib数据）

        Args:
            symbol: 股票代码
            date: 日期（YYYY-MM-DD），默认最新

        Returns:
            float: 收盘价，如果数据不存在返回None
        """
        csv_path = QLIB_DATA_DIR / f"{symbol}.csv"
        if not csv_path.exists():
            return None

        try:
            df = pd.read_csv(csv_path)
            if date:
                row = df[df['date'] == date]
                if not row.empty:
                    return float(row.iloc[0]['close'])
            else:
                # 最新价格
                return float(df.iloc[-1]['close'])
        except Exception:
            return None

        return None

    def buy(self, symbol: str, shares: int, price: float, name: str = "", date: Optional[str] = None):
        """
        买入股票

        Args:
            symbol: 股票代码
            shares: 股数（必须是100的倍数）
            price: 买入价格
            name: 股票名称
            date: 交易日期
        """
        if shares % 100 != 0:
            raise ValueError(f"股数必须是100的倍数，当前: {shares}")

        cost = shares * price
        if cost > self.cash:
            raise ValueError(f"资金不足：需要{cost:.2f}元，可用{self.cash:.2f}元")

        # 扣除资金
        self.cash -= cost

        # 更新持仓
        if symbol in self.holdings:
            # 已有持仓，计算新的成本基准
            old_shares = self.holdings[symbol]['shares']
            old_cost_basis = self.holdings[symbol]['cost_basis']
            new_cost_basis = (old_shares * old_cost_basis + shares * price) / (old_shares + shares)

            self.holdings[symbol]['shares'] += shares
            self.holdings[symbol]['cost_basis'] = new_cost_basis
        else:
            # 新建持仓
            self.holdings[symbol] = {
                'shares': shares,
                'cost_basis': price,
                'name': name
            }

        # 记录交易
        self._log_trade({
            'type': 'buy',
            'symbol': symbol,
            'name': name,
            'shares': shares,
            'price': price,
            'cost': cost,
            'date': date or datetime.now().strftime('%Y-%m-%d')
        })

        self._save_state()

    def sell(self, symbol: str, shares: int, price: float, date: Optional[str] = None):
        """
        卖出股票

        Args:
            symbol: 股票代码
            shares: 股数
            price: 卖出价格
            date: 交易日期
        """
        if symbol not in self.holdings:
            raise ValueError(f"未持有股票 {symbol}")

        if shares > self.holdings[symbol]['shares']:
            raise ValueError(f"持仓不足：需要{shares}股，持有{self.holdings[symbol]['shares']}股")

        # 计算收益
        cost_basis = self.holdings[symbol]['cost_basis']
        proceeds = shares * price
        cost = shares * cost_basis
        profit = proceeds - cost

        # 增加资金
        self.cash += proceeds

        # 更新持仓
        self.holdings[symbol]['shares'] -= shares
        if self.holdings[symbol]['shares'] == 0:
            name = self.holdings[symbol]['name']
            del self.holdings[symbol]
        else:
            name = self.holdings[symbol]['name']

        # 记录交易
        self._log_trade({
            'type': 'sell',
            'symbol': symbol,
            'name': name,
            'shares': shares,
            'price': price,
            'proceeds': proceeds,
            'cost': cost,
            'profit': profit,
            'profit_pct': (profit / cost * 100) if cost > 0 else 0,
            'date': date or datetime.now().strftime('%Y-%m-%d')
        })

        self._save_state()

    def rebalance(self, target_positions: List[Dict], date: Optional[str] = None):
        """
        月度再平衡（Phase 6D逻辑）

        Args:
            target_positions: 目标持仓列表 [{'symbol': ..., 'name': ..., 'price': ..., 'lots': ...}, ...]
            date: 再平衡日期
        """
        rebalance_date = date or datetime.now().strftime('%Y-%m-%d')

        # 1. 清仓所有现有持仓
        for symbol in list(self.holdings.keys()):
            shares = self.holdings[symbol]['shares']
            price = self._get_current_price(symbol, rebalance_date)

            if price is None:
                # 数据缺失，使用成本价
                price = self.holdings[symbol]['cost_basis']

            self.sell(symbol, shares, price, date=rebalance_date)

        # 2. 买入新持仓
        for position in target_positions:
            symbol = position['symbol']
            name = position.get('name', '')
            price = position['price']
            lots = position['lots']
            shares = lots * 100

            if shares > 0:
                try:
                    self.buy(symbol, shares, price, name, date=rebalance_date)
                except ValueError as e:
                    # 资金不足，跳过
                    print(f"⚠️ 跳过 {symbol}: {e}")
                    continue

        self.last_rebalance_date = rebalance_date
        self._save_state()

    def update_prices(self, date: Optional[str] = None) -> Dict:
        """
        更新持仓价格并计算收益

        Args:
            date: 更新日期，默认最新

        Returns:
            dict: {
                'total_value': float,  # 总市值
                'total_cost': float,   # 总成本
                'unrealized_pnl': float,  # 未实现盈亏
                'unrealized_pnl_pct': float,  # 未实现收益率
                'positions': List[Dict]  # 持仓明细
            }
        """
        update_date = date or datetime.now().strftime('%Y-%m-%d')

        positions = []
        total_value = self.cash
        total_cost = self.initial_cash - self.cash

        for symbol, holding in self.holdings.items():
            price = self._get_current_price(symbol, update_date)

            if price is None:
                # 数据缺失，使用成本价
                price = holding['cost_basis']

            shares = holding['shares']
            cost_basis = holding['cost_basis']
            market_value = shares * price
            cost = shares * cost_basis
            unrealized_pnl = market_value - cost
            unrealized_pnl_pct = (unrealized_pnl / cost * 100) if cost > 0 else 0

            positions.append({
                'symbol': symbol,
                'name': holding['name'],
                'shares': shares,
                'cost_basis': cost_basis,
                'current_price': price,
                'market_value': market_value,
                'cost': cost,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct
            })

            total_value += market_value

        unrealized_pnl = total_value - self.initial_cash
        unrealized_pnl_pct = (unrealized_pnl / self.initial_cash * 100) if self.initial_cash > 0 else 0

        return {
            'date': update_date,
            'total_value': total_value,
            'cash': self.cash,
            'holdings_value': total_value - self.cash,
            'total_cost': self.initial_cash,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': unrealized_pnl_pct,
            'positions': positions
        }

    def get_stats(self, date: Optional[str] = None) -> Dict:
        """
        获取持仓统计（封装update_prices，供API调用）

        Args:
            date: 统计日期

        Returns:
            dict: 持仓统计信息
        """
        return self.update_prices(date)

    def get_trade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        获取交易历史

        Args:
            limit: 返回最近N条记录，None表示全部

        Returns:
            list: 交易记录列表（按时间倒序）
        """
        if not TRADES_LOG_FILE.exists():
            return []

        trades = []
        with open(TRADES_LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                trades.append(json.loads(line))

        # 按时间倒序
        trades.reverse()

        if limit:
            trades = trades[:limit]

        return trades

    def reset(self, cash: float = 100000):
        """
        重置持仓（清空所有持仓和交易记录）

        Args:
            cash: 初始资金
        """
        self._initialize_state(cash)
        self._save_state()

        # 清空交易日志
        if TRADES_LOG_FILE.exists():
            TRADES_LOG_FILE.unlink()


# ===== 测试代码 =====
if __name__ == "__main__":
    print("测试 portfolio_manager.py...\n")

    # 测试1: 初始化持仓
    print("测试1: 初始化虚拟持仓")
    portfolio = VirtualPortfolio(initial_cash=100000, load_existing=False)
    print(f"✓ 初始资金: {portfolio.cash:.0f} 元")
    print(f"✓ 持仓数: {len(portfolio.holdings)}")

    # 测试2: 买入股票
    print("\n测试2: 买入股票")
    try:
        portfolio.buy('002920.SZ', 100, 153.0, '德赛西威', date='2025-01-15')
        print(f"✓ 买入成功")
        print(f"✓ 剩余资金: {portfolio.cash:.0f} 元")
        print(f"✓ 持仓数: {len(portfolio.holdings)}")
    except Exception as e:
        print(f"❌ 买入失败: {e}")

    # 测试3: 获取持仓统计
    print("\n测试3: 持仓统计")
    stats = portfolio.get_stats(date='2025-01-15')
    print(f"✓ 总市值: {stats['total_value']:.0f} 元")
    print(f"✓ 未实现盈亏: {stats['unrealized_pnl']:.2f} 元 ({stats['unrealized_pnl_pct']:.2f}%)")
    print(f"✓ 持仓明细: {len(stats['positions'])} 只")

    # 测试4: 交易历史
    print("\n测试4: 交易历史")
    trades = portfolio.get_trade_history(limit=5)
    print(f"✓ 交易记录数: {len(trades)}")
    if trades:
        print(f"✓ 最近一笔: {trades[0]['type']} {trades[0]['symbol']} {trades[0]['shares']}股")

    # 测试5: 重置
    print("\n测试5: 重置持仓")
    portfolio.reset(cash=100000)
    print(f"✓ 重置后资金: {portfolio.cash:.0f} 元")
    print(f"✓ 重置后持仓: {len(portfolio.holdings)}")

    print("\n✅ 测试完成")
