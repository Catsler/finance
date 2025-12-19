"""
股票标的池（Universe）工具函数

用于同步全市场股票列表（目前支持 A 股：上交所/深交所，可选北交所）。
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd


def disable_requests_proxy_from_env() -> None:
    """
    禁用环境变量中的代理设置。

    说明：
    - AKShare 内部使用 requests，会读取 HTTP(S)_PROXY 等环境变量；
    - 部分网络环境下代理不可用会导致请求失败，因此提供显式禁用。
    """
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        os.environ.pop(key, None)
    os.environ.setdefault("NO_PROXY", "*")


@dataclass(frozen=True)
class UniverseSyncConfig:
    include_bj: bool = False
    disable_proxy: bool = True
    max_retries: int = 3
    retry_backoff_sec: float = 1.5


def _with_retries(
    func: Callable[[], pd.DataFrame],
    *,
    max_retries: int,
    retry_backoff_sec: float,
    name: str,
) -> pd.DataFrame:
    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as exc:  # pragma: no cover (网络异常环境相关)
            last_error = exc
            if attempt >= max_retries - 1:
                raise
            time.sleep(retry_backoff_sec * (2**attempt))
    raise RuntimeError(f"{name} failed: {last_error}")


def fetch_a_share_universe(config: UniverseSyncConfig) -> pd.DataFrame:
    """
    从 AKShare 同步全量 A 股股票列表。

    返回列：
    - symbol: 统一代码（如 600519.SH / 000001.SZ / 920001.BJ）
    - code: 6位数字代码
    - name: 证券简称
    - exchange: SH/SZ/BJ
    - list_date: 上市日期（可为空）
    - board: 板块（可为空，如主板/科创板/创业板等）
    - industry: 行业（可为空）
    - source: 数据来源标识（akshare_sh / akshare_sz / akshare_bj）
    """
    if config.disable_proxy:
        disable_requests_proxy_from_env()

    import akshare as ak  # 延迟导入，避免无依赖时报错

    def fetch_sh_main() -> pd.DataFrame:
        return ak.stock_info_sh_name_code(symbol="主板A股")

    def fetch_sh_star() -> pd.DataFrame:
        return ak.stock_info_sh_name_code(symbol="科创板")

    def fetch_sz_all() -> pd.DataFrame:
        return ak.stock_info_sz_name_code(symbol="A股列表")

    sh_main = _with_retries(
        fetch_sh_main,
        max_retries=config.max_retries,
        retry_backoff_sec=config.retry_backoff_sec,
        name="akshare.stock_info_sh_name_code(主板A股)",
    )
    sh_star = _with_retries(
        fetch_sh_star,
        max_retries=config.max_retries,
        retry_backoff_sec=config.retry_backoff_sec,
        name="akshare.stock_info_sh_name_code(科创板)",
    )
    sz_all = _with_retries(
        fetch_sz_all,
        max_retries=config.max_retries,
        retry_backoff_sec=config.retry_backoff_sec,
        name="akshare.stock_info_sz_name_code(A股列表)",
    )

    # 上交所：主板A股 + 科创板
    sh_df = pd.concat([sh_main, sh_star], ignore_index=True)
    sh_df = sh_df.rename(
        columns={
            "证券代码": "code",
            "证券简称": "name",
            "上市日期": "list_date",
        }
    )
    sh_df["exchange"] = "SH"
    sh_df["symbol"] = sh_df["code"].astype(str).str.zfill(6) + ".SH"
    sh_df["board"] = ""
    sh_df["industry"] = ""
    sh_df["source"] = "akshare_sh"

    # 深交所：A股列表（含主板/中小板/创业板）
    sz_df = sz_all.rename(
        columns={
            "A股代码": "code",
            "A股简称": "name",
            "A股上市日期": "list_date",
            "所属行业": "industry",
            "板块": "board",
        }
    )
    sz_df["exchange"] = "SZ"
    sz_df["symbol"] = sz_df["code"].astype(str).str.zfill(6) + ".SZ"
    sz_df["source"] = "akshare_sz"

    frames = [sh_df[["symbol", "code", "name", "exchange", "list_date", "board", "industry", "source"]]]
    frames.append(sz_df[["symbol", "code", "name", "exchange", "list_date", "board", "industry", "source"]])

    # 北交所：可选（部分系统不支持 .BJ 数据下载，仅做列表同步）
    if config.include_bj and hasattr(ak, "stock_info_bj_name_code"):
        def fetch_bj() -> pd.DataFrame:
            return ak.stock_info_bj_name_code()

        bj_df = _with_retries(
            fetch_bj,
            max_retries=config.max_retries,
            retry_backoff_sec=config.retry_backoff_sec,
            name="akshare.stock_info_bj_name_code()",
        )
        bj_df = bj_df.rename(
            columns={
                "证券代码": "code",
                "证券简称": "name",
                "上市日期": "list_date",
                "所属行业": "industry",
            }
        )
        bj_df["exchange"] = "BJ"
        bj_df["symbol"] = bj_df["code"].astype(str).str.zfill(6) + ".BJ"
        bj_df["board"] = ""
        bj_df["source"] = "akshare_bj"

        frames.append(bj_df[["symbol", "code", "name", "exchange", "list_date", "board", "industry", "source"]])

    universe = pd.concat(frames, ignore_index=True)
    universe = universe.drop_duplicates(subset=["symbol"]).sort_values("symbol").reset_index(drop=True)

    # 规范日期字段（允许为空）
    universe["list_date"] = pd.to_datetime(universe["list_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    universe["list_date"] = universe["list_date"].fillna("")

    return universe

