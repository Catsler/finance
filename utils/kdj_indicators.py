from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class KdjParams:
    n: int = 9
    k_smooth: int = 3
    d_smooth: int = 3


def add_ma20_60m(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ma20"] = out["close"].rolling(window=20, min_periods=20).mean()
    return out


def add_kdj(df: pd.DataFrame, params: KdjParams = KdjParams()) -> pd.DataFrame:
    """
    KDJ(9,3,3) implementation:
      RSV = (C - LLV(N)) / (HHV(N) - LLV(N)) * 100
      K = 2/3 * K_prev + 1/3 * RSV
      D = 2/3 * D_prev + 1/3 * K
      J = 3*K - 2*D

    Initializes K=D=50.
    """
    out = df.copy()
    low_n = out["low"].rolling(window=params.n, min_periods=params.n).min()
    high_n = out["high"].rolling(window=params.n, min_periods=params.n).max()
    denom = (high_n - low_n)
    rsv = (out["close"] - low_n) / denom.replace(0, pd.NA) * 100
    rsv = rsv.fillna(50.0)

    k_vals = []
    d_vals = []
    k_prev = 50.0
    d_prev = 50.0
    for v in rsv.tolist():
        k = (2 / 3) * k_prev + (1 / 3) * float(v)
        d = (2 / 3) * d_prev + (1 / 3) * k
        k_vals.append(k)
        d_vals.append(d)
        k_prev, d_prev = k, d

    out["k"] = k_vals
    out["d"] = d_vals
    out["j"] = out["k"] * 3 - out["d"] * 2
    return out


def prepare_60m_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_kdj(df)
    df = add_ma20_60m(df)
    return df


def last_completed_bar(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None
    return df.iloc[-1]

