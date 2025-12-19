from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fees:
    commission: float
    stamp_tax: float
    transfer_fee: float

    @property
    def total(self) -> float:
        return self.commission + self.stamp_tax + self.transfer_fee


def calc_fees(trade_value: float, direction: str, market: str) -> Fees:
    commission = max(trade_value * 0.00025, 5.0)
    stamp_tax = trade_value * 0.001 if direction == "SELL" else 0.0
    transfer_fee = trade_value * 0.00002 if market == "SH" else 0.0
    return Fees(commission=commission, stamp_tax=stamp_tax, transfer_fee=transfer_fee)

