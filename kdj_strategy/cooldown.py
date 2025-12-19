"""
冷却机制与每日限额管理
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Set
from pathlib import Path
import json


class CooldownManager:
    """管理信号冷却和每日限额"""
    
    def __init__(
        self,
        cooldown_minutes: int = 60,
        daily_limit: int = 3,
        state_file: Path = Path('data/cooldown_state.json'),
    ):
        """
        Args:
            cooldown_minutes: 同标的冷却时间（分钟）
            daily_limit: 每日每标的最多信号数
            state_file: 状态持久化文件
        """
        self.cooldown_minutes = cooldown_minutes
        self.daily_limit = daily_limit
        self.state_file = state_file
        
        # 内存状态
        self.last_signal_time: Dict[str, datetime] = {}  # symbol -> last_time
        self.daily_count: Dict[str, int] = {}  # symbol -> count
        self.last_reset_date: str = datetime.now().strftime('%Y-%m-%d')
        
        # 加载状态
        self._load_state()
    
    def can_signal(self, symbol: str) -> tuple[bool, str]:
        """
        检查是否可以生成信号
        
        Args:
            symbol: 股票代码
            
        Returns:
            (allowed, reason)
        """
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 日切检查
        if today != self.last_reset_date:
            self._reset_daily()
        
        # 检查每日限额
        count = self.daily_count.get(symbol, 0)
        if count >= self.daily_limit:
            return False, f'达到每日限额 {self.daily_limit}'
        
        # 检查冷却时间
        last_time = self.last_signal_time.get(symbol)
        if last_time:
            elapsed = (now - last_time).total_seconds() / 60
            if elapsed < self.cooldown_minutes:
                remaining = self.cooldown_minutes - elapsed
                return False, f'冷却中，还需 {remaining:.0f} 分钟'
        
        return True, ''
    
    def record_signal(self, symbol: str):
        """记录信号生成"""
        now = datetime.now()
        self.last_signal_time[symbol] = now
        self.daily_count[symbol] = self.daily_count.get(symbol, 0) + 1
        self._save_state()
    
    def _reset_daily(self):
        """日切重置"""
        self.daily_count.clear()
        self.last_reset_date = datetime.now().strftime('%Y-%m-%d')
        self._save_state()
    
    def _load_state(self):
        """从文件加载状态"""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # 恢复状态
            self.last_reset_date = state.get('last_reset_date', self.last_reset_date)
            self.daily_count = state.get('daily_count', {})
            
            # 恢复时间（字符串 -> datetime）
            last_times = state.get('last_signal_time', {})
            for symbol, timestr in last_times.items():
                self.last_signal_time[symbol] = datetime.fromisoformat(timestr)
        
        except Exception as e:
            print(f'加载冷却状态失败: {e}')
    
    def _save_state(self):
        """保存状态到文件"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换时间为字符串
        last_times = {
            symbol: dt.isoformat()
            for symbol, dt in self.last_signal_time.items()
        }
        
        state = {
            'last_reset_date': self.last_reset_date,
            'daily_count': self.daily_count,
            'last_signal_time': last_times,
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
