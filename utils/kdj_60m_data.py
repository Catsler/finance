from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


class KdjDataError(RuntimeError):
    pass


def _cache_dir() -> Path:
    d = Path("data/cache/kdj_60m")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_paths(symbol: str) -> tuple[Path, Path]:
    safe = symbol.replace(".", "_")
    csv_path = _cache_dir() / f"{safe}.csv"
    meta_path = _cache_dir() / f"{safe}.meta.json"
    return csv_path, meta_path


def _is_cache_fresh(meta_path: Path, ttl_seconds: int) -> bool:
    if ttl_seconds <= 0 or not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        fetched_at = float(meta.get("fetched_at", 0))
        return (time.time() - fetched_at) <= ttl_seconds
    except Exception:
        return False


def _normalize_hist_min_df(df: pd.DataFrame) -> pd.DataFrame:
    # AKShare may return either Chinese columns or already normalized.
    rename_map = {
        "时间": "datetime",
        "日期": "datetime",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df = df.rename(columns={k: v})

    required = ["datetime", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KdjDataError(f"60m data missing columns: {missing}")

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df = df.dropna(subset=["datetime", "open", "high", "low", "close"]).sort_values("datetime")
    df = df.reset_index(drop=True)
    return df


@dataclass(frozen=True)
class Kdj60mDataFetcher:
    cache_ttl_seconds: int = 3600

    def fetch(self, symbol: str) -> pd.DataFrame:
        """
        Fetch 60-minute bars for A-share symbol (e.g. 000001.SZ), using AKShare with local file cache.
        """
        csv_path, meta_path = _cache_paths(symbol)
        if _is_cache_fresh(meta_path, self.cache_ttl_seconds) and csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                df = _normalize_hist_min_df(df)
                return df
            except Exception:
                pass

        try:
            import akshare as ak  # type: ignore
        except ImportError as e:
            raise KdjDataError("akshare not installed; install requirements_kdj_strategy.txt") from e

        code = symbol.replace(".SZ", "").replace(".SH", "")

        # AKShare: Eastmoney minute/hours bars (period in minutes as string).
        try:
            raw = ak.stock_zh_a_hist_min_em(symbol=code, period="60", adjust="")  # type: ignore[attr-defined]
        except Exception as e:
            raise KdjDataError(f"AKShare 60m fetch failed for {symbol}: {e}") from e

        if raw is None or getattr(raw, "empty", True):
            raise KdjDataError(f"No 60m data returned for {symbol}")

        df = _normalize_hist_min_df(raw)

        # Persist cache
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        meta_path.write_text(
            json.dumps(
                {
                    "symbol": symbol,
                    "fetched_at": time.time(),
                    "source": "ak.stock_zh_a_hist_min_em(period=60,adjust='')",
                    "rows": len(df),
                    "min_datetime": str(df["datetime"].min()),
                    "max_datetime": str(df["datetime"].max()),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return df

