"""
Paper Trading API 客户端
"""
from __future__ import annotations

import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Position:
    """持仓"""
    symbol: str
    total_quantity: int
    available_quantity: int
    avg_cost: float


class PaperTradingClient:
    """Paper Trading API 客户端"""
    
    def __init__(self, base_url: str = 'http://127.0.0.1:8000/api/v1'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_account(self) -> Dict[str, Any]:
        """获取账户信息"""
        resp = self.session.get(f'{self.base_url}/account')
        resp.raise_for_status()
        return resp.json()
    
    def get_positions(self) -> List[Position]:
        """获取持仓列表"""
        resp = self.session.get(f'{self.base_url}/positions')
        resp.raise_for_status()
        data = resp.json()
        return [Position(**p) for p in data]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取单个持仓"""
        positions = self.get_positions()
        for p in positions:
            if p.symbol == symbol:
                return p
        return None
    
    def place_order(
        self,
        symbol: str,
        direction: str,
        quantity: int,
        order_type: str = 'AGGRESSIVE',
        limit_price: Optional[float] = None,
        signal_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        下单
        
        Args:
            symbol: 股票代码
            direction: BUY / SELL
            quantity: 股数
            order_type: AGGRESSIVE / LIMIT
            limit_price: 限价（LIMIT时必填）
            signal_type: 信号类型（可选）
            
        Returns:
            响应数据（包含 client_order_id, status 等）
        """
        payload = {
            'symbol': symbol,
            'direction': direction,
            'quantity': quantity,
            'order_type': order_type,
        }
        
        if limit_price is not None:
            payload['limit_price'] = limit_price
        
        if signal_type:
            payload['signal_type'] = signal_type
        
        resp = self.session.post(f'{self.base_url}/orders', json=payload)
        resp.raise_for_status()
        return resp.json()
    
    def get_orders(self, status: Optional[str] = None, limit: int = 200) -> List[Dict]:
        """获取订单列表"""
        params = {'limit': limit}
        if status:
            params['status'] = status
        
        resp = self.session.get(f'{self.base_url}/orders', params=params)
        resp.raise_for_status()
        return resp.json()
    
    def cancel_order(self, client_order_id: str) -> Dict[str, Any]:
        """撤单"""
        resp = self.session.post(f'{self.base_url}/orders/{client_order_id}/cancel')
        resp.raise_for_status()
        return resp.json()
    
    def get_kill_switch_status(self) -> bool:
        """获取 Kill Switch 状态"""
        resp = self.session.get(f'{self.base_url}/risk/kill_switch')
        resp.raise_for_status()
        return resp.json().get('enabled', False)
    
    def set_kill_switch(self, enabled: bool) -> Dict[str, Any]:
        """设置 Kill Switch"""
        resp = self.session.post(
            f'{self.base_url}/risk/kill_switch',
            json={'enabled': enabled}
        )
        resp.raise_for_status()
        return resp.json()
