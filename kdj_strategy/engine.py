"""
策略主引擎：扫描信号 + 下单
"""
from __future__ import annotations

from pathlib import Path
from typing import List
import pandas as pd
from datetime import datetime

from .data_60m import get_60m_kline
from .indicators import add_all_indicators
from .signals import SignalGenerator, Signal
from .cooldown import CooldownManager
from .client import PaperTradingClient


class StrategyEngine:
    """KDJ 策略引擎"""
    
    def __init__(
        self,
        symbols: List[str],
        api_base_url: str = 'http://127.0.0.1:8000/api/v1',
        auto_trade: bool = False,
        signal_log_dir: Path = Path('data/signals'),
    ):
        """
        Args:
            symbols: 监控的股票列表
            api_base_url: Paper Trading API 地址
            auto_trade: 是否自动下单（False=仅生成信号）
            signal_log_dir: 信号日志目录
        """
        self.symbols = symbols
        self.auto_trade = auto_trade
        self.signal_log_dir = signal_log_dir
        
        # 初始化组件
        self.signal_gen = SignalGenerator(
            buy_threshold=25,
            sell_threshold=75,
            min_range=0.02,
            quantity=400,
        )
        self.cooldown = CooldownManager(
            cooldown_minutes=60,
            daily_limit=3,
        )
        self.client = PaperTradingClient(base_url=api_base_url)
        
        # 确保日志目录存在
        self.signal_log_dir.mkdir(parents=True, exist_ok=True)
    
    def scan_signals(self) -> List[Signal]:
        """
        扫描所有标的，生成信号
        
        Returns:
            信号列表
        """
        signals = []
        
        for symbol in self.symbols:
            try:
                signal = self._scan_single(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                print(f'扫描 {symbol} 失败: {e}')
        
        return signals
    
    def _scan_single(self, symbol: str) -> Signal | None:
        """扫描单个标的"""
        # 检查冷却
        allowed, reason = self.cooldown.can_signal(symbol)
        if not allowed:
            print(f'{symbol}: {reason}')
            return None
        
        # 获取 60 分钟数据
        df = get_60m_kline(symbol, use_cache=True)
        if df.empty:
            print(f'{symbol}: 无数据')
            return None
        
        # 计算指标
        df = add_all_indicators(df)
        
        # 生成信号
        signal = self.signal_gen.generate_signal(symbol, df)
        
        if signal:
            # 额外检查：如果是卖出，检查是否有持仓
            if signal.direction == 'SELL':
                position = self.client.get_position(symbol)
                if not position or position.available_quantity < signal.quantity:
                    print(f'{symbol}: 无足够可卖仓位')
                    return None
            
            # 记录冷却
            self.cooldown.record_signal(symbol)
            
            # 保存信号日志
            self._log_signal(signal)
            
            print(f'✅ 信号: {signal.symbol} {signal.direction} {signal.quantity} | {signal.reason}')
        
        return signal
    
    def execute_signal(self, signal: Signal) -> bool:
        """
        执行信号（下单）
        
        Args:
            signal: 信号
            
        Returns:
            是否成功
        """
        try:
            result = self.client.place_order(
                symbol=signal.symbol,
                direction=signal.direction,
                quantity=signal.quantity,
                order_type='AGGRESSIVE',
                signal_type=signal.signal_type,
            )
            
            print(f'下单成功: {signal.symbol} {signal.direction} {signal.quantity}')
            print(f'  Order ID: {result.get("client_order_id")}')
            print(f'  Status: {result.get("status")}')
            
            return True
        
        except Exception as e:
            print(f'下单失败: {signal.symbol} {signal.direction} {signal.quantity} | {e}')
            return False
    
    def run_once(self):
        """单次扫描运行"""
        print(f'\n=== {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} 开始扫描 ===')
        
        # 检查 Kill Switch
        if self.client.get_kill_switch_status():
            print('⚠️ Kill Switch 已启用，跳过交易')
            return
        
        # 扫描信号
        signals = self.scan_signals()
        
        if not signals:
            print('无新信号')
            return
        
        # 执行信号
        if self.auto_trade:
            for signal in signals:
                self.execute_signal(signal)
        else:
            print(f'\n📋 生成 {len(signals)} 个信号（半自动模式，需人工确认）:')
            for signal in signals:
                print(f'  - {signal.symbol} {signal.direction} {signal.quantity} @ {signal.signal_time.strftime("%H:%M")}')
    
    def _log_signal(self, signal: Signal):
        """记录信号到日志文件"""
        log_file = self.signal_log_dir / f'{datetime.now().strftime("%Y%m%d")}_signals.csv'
        
        # 准备数据
        data = {
            'signal_time': signal.signal_time.isoformat(),
            'symbol': signal.symbol,
            'direction': signal.direction,
            'quantity': signal.quantity,
            'signal_type': signal.signal_type,
            'reason': signal.reason,
            'J': signal.J,
            'K': signal.K,
            'D': signal.D,
            'close': signal.close,
            'MA20': signal.MA20,
            'intraday_range': signal.intraday_range,
        }
        
        # 追加到 CSV
        df = pd.DataFrame([data])
        if log_file.exists():
            df.to_csv(log_file, mode='a', header=False, index=False)
        else:
            df.to_csv(log_file, mode='w', header=True, index=False)
