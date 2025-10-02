#!/usr/bin/env python3
"""
AKShare → Qlib 数据转换脚本（Phase 0 MVP）

用法示例：
    # 命令行调用
    python scripts/akshare-to-qlib-converter.py --symbol 000001.SZ --years 3
    python scripts/akshare-to-qlib-converter.py --symbol 000858.SZ --start 2022-01-01

    # Python 代码调用
    from akshare_to_qlib_converter import download_and_convert
    download_and_convert("000001.SZ", years=3)

输出：
    - CSV 数据文件：~/.qlib/qlib_data/cn_data/000001.SZ.csv
    - 验证日志：./validation_report.log

验证规则：
    - 缺失率 < 5%（基于预期交易日数）
    - 所有收盘价 > 0
    - 累计成交量 > 0

注意：
    - Phase 0 使用 CSV 格式（便于验证）
    - Phase 1 可考虑转换为 Qlib bin 格式（性能优化）
"""

import argparse
import logging
import time
from pathlib import Path
from typing import Optional

import akshare as ak
import pandas as pd

# ============================================
# 配置常量
# ============================================

LOG_PATH = Path("validation_report.log")
QLIB_ROOT = Path.home() / ".qlib" / "qlib_data" / "cn_data"
EXPECTED_TRADING_DAYS_PER_YEAR = 252
MISSING_RATE_THRESHOLD = 0.05  # 5%

# ============================================
# 核心函数
# ============================================


def fetch_with_akshare(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years: int = 3,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    从 AKShare 获取股票历史数据（后复权）

    参数：
        symbol: 股票代码，如 "000001.SZ" 或 "600000.SH"
        start_date: 起始日期，格式 "YYYY-MM-DD"（可选）
        end_date: 结束日期，格式 "YYYY-MM-DD"（可选）
        years: 回溯年数（当 start_date 未指定时生效）
        max_retries: 最大重试次数

    返回：
        DataFrame，包含字段：date, open, close, high, low, volume, money

    异常：
        ValueError: 数据获取失败或返回为空
    """

    # 提取纯数字代码（去掉 .SZ/.SH 后缀）
    code = symbol.replace(".SZ", "").replace(".SH", "")

    # 计算起始日期
    if start_date:
        start_str = start_date.replace("-", "")
    elif years:
        start_dt = pd.Timestamp.today() - pd.DateOffset(years=years)
        start_str = start_dt.strftime("%Y%m%d")
    else:
        raise ValueError("必须指定 start_date 或 years 参数")

    end_str = (
        end_date.replace("-", "") if end_date else pd.Timestamp.today().strftime("%Y%m%d")
    )

    # 重试逻辑（指数退避）
    for attempt in range(max_retries):
        try:
            logging.info("正在获取 %s 数据（%s ~ %s）...", symbol, start_str, end_str)

            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="hfq",  # 后复权（历史复权）
            )

            if df is None or df.empty:
                raise ValueError(f"AKShare 未返回数据：{symbol}")

            # 字段重命名（AKShare → Qlib 标准字段）
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "money",
                }
            )

            # 数据类型转换
            df["date"] = pd.to_datetime(df["date"])
            for col in ["open", "close", "high", "low", "volume", "money"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # 排序并重置索引
            df = df.sort_values("date").reset_index(drop=True)

            logging.info("成功获取 %d 条记录", len(df))
            return df

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # 指数退避：2s, 4s, 8s
                logging.warning(
                    "第 %d 次尝试失败，%d 秒后重试: %s", attempt + 1, wait_time, e
                )
                time.sleep(wait_time)
            else:
                logging.error("所有重试失败: %s", e)
                raise


def validate_dataframe(
    df: pd.DataFrame, symbol: str, expected_trading_days: int = 730
) -> None:
    """
    验证数据质量

    参数：
        df: 待验证的 DataFrame
        symbol: 股票代码（用于日志）
        expected_trading_days: 预期交易日数（默认 3 年约 730 天）

    异常：
        ValueError: 数据质量不符合要求
    """
    actual_days = len(df)
    missing_rate = max(0.0, 1 - actual_days / expected_trading_days)
    close_min = df["close"].min()
    close_max = df["close"].max()
    volume_sum = df["volume"].sum()

    logging.info(
        "%s | 记录数=%d | 缺失率=%.2f%% | 价格范围=[%.2f, %.2f] | 总成交量=%.0f",
        symbol,
        actual_days,
        missing_rate * 100,
        close_min,
        close_max,
        volume_sum,
    )

    # 验证规则
    errors = []

    if missing_rate >= MISSING_RATE_THRESHOLD:
        errors.append(f"缺失率 {missing_rate:.2%} 超过 {MISSING_RATE_THRESHOLD:.0%} 阈值")

    if close_min <= 0:
        errors.append(f"存在非正收盘价: {close_min}")

    if volume_sum <= 0:
        errors.append("累计成交量为 0")

    # 额外检查：NaN 值
    nan_counts = df[["open", "close", "high", "low", "volume"]].isna().sum()
    if nan_counts.any():
        errors.append(f"存在 NaN 值: {nan_counts[nan_counts > 0].to_dict()}")

    if errors:
        error_msg = "; ".join(errors)
        logging.error("✗ %s 验证失败: %s", symbol, error_msg)
        raise ValueError(f"{symbol} 数据质量不合格: {error_msg}")

    logging.info("✓ %s 数据验证通过", symbol)


def save_to_csv(df: pd.DataFrame, symbol: str, output_root: Path) -> Path:
    """
    保存为 CSV 格式

    注意：Phase 0 暂时使用 CSV 格式，Phase 1 可转换为 Qlib bin 格式

    参数：
        df: 待保存的 DataFrame
        symbol: 股票代码（用于文件名）
        output_root: 输出目录

    返回：
        保存的 CSV 文件路径
    """
    output_root.mkdir(parents=True, exist_ok=True)
    csv_file = output_root / f"{symbol}.csv"

    # 设置 date 为索引
    df = df.set_index("date")

    # 只保存必要的字段
    df[["open", "close", "high", "low", "volume", "money"]].to_csv(csv_file)

    logging.info("数据已保存: %s (%.2f KB)", csv_file, csv_file.stat().st_size / 1024)
    return csv_file


def download_and_convert(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years: int = 3,
    output_root: Optional[str] = None,
) -> Path:
    """
    完整流程：下载 → 验证 → 保存

    参数：
        symbol: 股票代码，如 "000001.SZ"
        start_date: 起始日期 "YYYY-MM-DD"（可选）
        end_date: 结束日期 "YYYY-MM-DD"（可选）
        years: 回溯年数（默认 3 年）
        output_root: 输出目录（默认 ~/.qlib/qlib_data/cn_data）

    返回：
        保存的 CSV 文件路径

    异常：
        ValueError: 数据获取或验证失败
    """
    output_root = Path(output_root or QLIB_ROOT).expanduser().resolve()

    # 1. 下载数据
    df = fetch_with_akshare(symbol, start_date, end_date, years)

    # 2. 验证数据
    expected_days = EXPECTED_TRADING_DAYS_PER_YEAR * years
    validate_dataframe(df, symbol, expected_days)

    # 3. 保存数据
    return save_to_csv(df, symbol, output_root)


# ============================================
# 命令行接口
# ============================================


def main() -> None:
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="AKShare → Qlib 数据转换（Phase 0 MVP）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/akshare-to-qlib-converter.py --symbol 000001.SZ --years 3
  python scripts/akshare-to-qlib-converter.py --symbol 000858.SZ --start 2022-01-01 --end 2024-12-31

输出：
  - CSV 文件：~/.qlib/qlib_data/cn_data/000001.SZ.csv
  - 验证日志：validation_report.log
        """,
    )

    parser.add_argument(
        "--symbol", required=True, help="股票代码，如 000001.SZ 或 600000.SH"
    )
    parser.add_argument(
        "--start", dest="start_date", help="起始日期 YYYY-MM-DD（可选，优先于 --years）"
    )
    parser.add_argument("--end", dest="end_date", help="结束日期 YYYY-MM-DD（可选）")
    parser.add_argument(
        "--years", type=int, default=3, help="回溯年数（默认 3 年，当 --start 未指定时生效）"
    )
    parser.add_argument(
        "--output-root", default=str(QLIB_ROOT), help=f"输出目录（默认 {QLIB_ROOT}）"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别（默认 INFO）",
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    try:
        logging.info("=" * 60)
        logging.info("Stock 数据转换工具 - Phase 0")
        logging.info("=" * 60)

        csv_file = download_and_convert(
            args.symbol, args.start_date, args.end_date, args.years, args.output_root
        )

        logging.info("=" * 60)
        logging.info("✅ Validation Passed: %s → %s", args.symbol, csv_file)
        logging.info("=" * 60)

    except Exception as e:
        logging.error("=" * 60)
        logging.error("❌ Validation Failed: %s", e)
        logging.error("=" * 60)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
