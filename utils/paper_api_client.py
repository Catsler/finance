from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import requests


class PaperApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class PaperApiClient:
    base_url: str = "http://127.0.0.1:8000/api/v1"
    timeout_seconds: int = 10

    def get_quotes(self, symbols: Iterable[str]) -> dict[str, dict[str, Any]]:
        symbols_list = [s for s in symbols]
        if not symbols_list:
            return {}

        resp = requests.get(
            f"{self.base_url}/quotes",
            params={"symbols": ",".join(symbols_list)},
            timeout=self.timeout_seconds,
        )
        if resp.status_code != 200:
            raise PaperApiError(f"GET /quotes failed: {resp.status_code} {resp.text}")

        data = resp.json()
        out: dict[str, dict[str, Any]] = {}
        for q in data:
            symbol = q.get("symbol")
            if symbol:
                out[symbol] = q
        return out

    def get_positions(self) -> dict[str, dict[str, Any]]:
        resp = requests.get(f"{self.base_url}/positions", timeout=self.timeout_seconds)
        if resp.status_code != 200:
            raise PaperApiError(f"GET /positions failed: {resp.status_code} {resp.text}")
        out: dict[str, dict[str, Any]] = {}
        for p in resp.json():
            out[p["symbol"]] = p
        return out

    def get_kill_switch(self) -> dict[str, Any]:
        resp = requests.get(f"{self.base_url}/risk/kill_switch", timeout=self.timeout_seconds)
        if resp.status_code != 200:
            raise PaperApiError(f"GET /risk/kill_switch failed: {resp.status_code} {resp.text}")
        return resp.json()

    def create_order(
        self,
        *,
        symbol: str,
        direction: str,
        quantity: int,
        order_type: str = "AGGRESSIVE",
        limit_price: float | None = None,
        signal_type: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": symbol,
            "direction": direction,
            "quantity": quantity,
            "order_type": order_type,
        }
        if limit_price is not None:
            payload["limit_price"] = limit_price
        if signal_type is not None:
            payload["signal_type"] = signal_type

        resp = requests.post(f"{self.base_url}/orders", json=payload, timeout=self.timeout_seconds)
        if resp.status_code != 200:
            raise PaperApiError(f"POST /orders failed: {resp.status_code} {resp.text}")
        return resp.json()

