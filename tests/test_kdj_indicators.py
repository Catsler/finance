#!/usr/bin/env python3
"""
MVP2-A: KDJ indicator unit tests

Run:
  python tests/test_kdj_indicators.py
"""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.kdj_indicators import add_kdj, add_ma20_60m


def test_kdj_basic_shape():
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01 09:30:00", periods=30, freq="60min"),
            "open": [10.0] * 30,
            "high": [10.5] * 30,
            "low": [9.5] * 30,
            "close": [10.0] * 30,
        }
    )
    out = add_kdj(df)
    assert len(out) == 30
    assert "k" in out.columns and "d" in out.columns and "j" in out.columns
    assert out["k"].notna().all()
    assert out["d"].notna().all()
    assert out["j"].notna().all()


def test_ma20_requires_20_bars():
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01 09:30:00", periods=25, freq="60min"),
            "open": [10.0] * 25,
            "high": [10.5] * 25,
            "low": [9.5] * 25,
            "close": list(range(25)),
        }
    )
    out = add_ma20_60m(df)
    assert out["ma20"].isna().sum() == 19
    assert out["ma20"].iloc[19] is not None


def run_all_tests():
    tests = [
        test_kdj_basic_shape,
        test_ma20_requires_20_bars,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {t.__name__}: {e}")
            failed += 1
    print(f"\npassed={passed} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())

