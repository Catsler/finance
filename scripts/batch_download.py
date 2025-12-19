#!/usr/bin/env python3
"""
批量下载股票数据脚本（支持并行下载和断点续传）

用法：
    # 串行下载（默认）
    python scripts/batch_download.py --years 3

    # 并行下载（推荐5线程）
    python scripts/batch_download.py --years 3 --parallel 5

    # 断点续传（跳过已下载）
    python scripts/batch_download.py --years 3 --resume --parallel 5

功能：
    - 从 stock_pool.yaml 读取股票列表
    - 支持并行下载（concurrent.futures.ThreadPoolExecutor）
    - 支持断点续传（检查已存在的数据文件）
    - 生成下载报告（JSON + Markdown）
"""

import argparse
import subprocess
import time
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import pandas as pd

# 添加项目根目录到路径，以便导入配置系统
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入配置系统和IO工具
from config import get_settings, Settings
from utils.io import save_json_with_metadata

# tqdm进度条支持
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("⚠️  tqdm未安装，将不显示进度条（可选安装: pip install tqdm）")


def load_stock_pool(pool_name: str = 'medium_cap', settings: Settings = None) -> list:
    """
    从配置系统加载股票池（已迁移到Pydantic Settings）

    Args:
        pool_name: 股票池名称（small_cap/medium_cap/legacy_test_pool）
        settings: Settings实例（可选，如不提供则自动加载）

    Returns:
        list: 股票信息列表（dict格式以保持向后兼容）
    """
    # 获取配置
    if settings is None:
        settings = get_settings()

    try:
        # 从配置系统获取股票池
        stock_list = settings.stock_pool.get_pool(pool_name)

        # 转换为dict列表以保持向后兼容
        stocks = [
            {
                "symbol": stock.symbol,
                "name": stock.name,
                "industry": stock.industry,
                "sector": stock.sector
            }
            for stock in stock_list
        ]

        if not stocks:
            print(f"❌ 股票池 {pool_name} 为空")
            sys.exit(1)

        print(f"✅ 从配置系统加载 {pool_name}（{len(stocks)} 只股票）")
        return stocks

    except Exception as e:
        print(f"❌ 加载股票池失败: {e}")
        sys.exit(1)


def is_already_downloaded(symbol: str, min_records: int = 500) -> bool:
    """
    检查股票数据是否已存在且完整

    Args:
        symbol: 股票代码（如 000001.SZ）
        min_records: 最小记录数阈值（默认500，约2年数据）

    Returns:
        bool: 如果数据存在且记录数>=min_records，返回True
    """
    csv_path = Path.home() / ".qlib" / "qlib_data" / "cn_data" / f"{symbol}.csv"

    if not csv_path.exists():
        return False

    try:
        df = pd.read_csv(csv_path)
        return len(df) >= min_records
    except Exception:
        # 如果文件损坏，视为未下载
        return False


def download_stock(symbol: str, years: int, silent: bool = False) -> dict:
    """
    下载单只股票数据

    Args:
        symbol: 股票代码
        years: 回溯年数
        silent: 是否静默模式（并行下载时使用）

    Returns:
        dict: 下载结果 {symbol, status, elapsed, message}
    """
    if not silent:
        print(f"\n{'='*60}")
        print(f"正在下载: {symbol}")
        print(f"{'='*60}")

    start_time = time.time()

    try:
        result = subprocess.run(
            [
                "python3",
                "scripts/akshare-to-qlib-converter.py",
                "--symbol", symbol,
                "--years", str(years),
                "--adjust", "qfq",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            if not silent:
                print(f"✅ {symbol} 下载成功 (耗时 {elapsed:.1f}s)")
            return {
                "symbol": symbol,
                "status": "success",
                "elapsed": elapsed,
                "message": "下载成功"
            }
        else:
            if not silent:
                print(f"❌ {symbol} 下载失败")
                print(f"错误: {result.stderr}")
            return {
                "symbol": symbol,
                "status": "failed",
                "elapsed": elapsed,
                "message": result.stderr.strip()[:200]  # 限制错误信息长度
            }

    except subprocess.TimeoutExpired:
        if not silent:
            print(f"❌ {symbol} 下载超时 (>120s)")
        return {
            "symbol": symbol,
            "status": "timeout",
            "elapsed": 120,
            "message": "下载超时"
        }
    except Exception as e:
        if not silent:
            print(f"❌ {symbol} 下载出错: {e}")
        return {
            "symbol": symbol,
            "status": "error",
            "elapsed": 0,
            "message": str(e)
        }


def download_with_parallel(stocks: List[dict], years: int, max_workers: int = 3,
                          resume: bool = False) -> List[dict]:
    """
    并行下载多只股票

    Args:
        stocks: 股票列表
        years: 回溯年数
        max_workers: 最大并发线程数（默认3，推荐3-5）
        resume: 是否启用断点续传

    Returns:
        List[dict]: 下载结果列表
    """
    results = []
    total = len(stocks)

    # 过滤已下载的股票（如启用resume）
    if resume:
        print("\n🔍 检查已下载的股票...")
        to_download = []
        skipped = []

        for stock in stocks:
            symbol = stock["symbol"]
            if is_already_downloaded(symbol, min_records=500):
                skipped.append(symbol)
                results.append({
                    "symbol": symbol,
                    "status": "skipped",
                    "elapsed": 0,
                    "message": "已存在，跳过"
                })
            else:
                to_download.append(stock)

        print(f"✅ 已下载: {len(skipped)} 只")
        print(f"📥 待下载: {len(to_download)} 只")

        if not to_download:
            print("\n🎉 所有股票已下载完成！")
            return results
    else:
        to_download = stocks

    # 并行下载
    print(f"\n🚀 开始并行下载（{max_workers} 线程）...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(download_stock, stock["symbol"], years, silent=True): stock
            for stock in to_download
        }

        # 使用进度条（如果可用）
        if TQDM_AVAILABLE:
            iterator = tqdm(as_completed(futures), total=len(to_download),
                          desc="下载进度", unit="只")
        else:
            iterator = as_completed(futures)

        # 收集结果
        for future in iterator:
            stock = futures[future]
            try:
                result = future.result()
                results.append(result)

                # 实时显示结果
                status_emoji = "✅" if result["status"] == "success" else "❌"
                if not TQDM_AVAILABLE:
                    print(f"{status_emoji} {result['symbol']} - {result['status']}")

            except Exception as e:
                # 异常处理
                results.append({
                    "symbol": stock["symbol"],
                    "status": "error",
                    "elapsed": 0,
                    "message": f"线程异常: {str(e)}"
                })

        # 添加短暂延迟，避免API限流
        time.sleep(1)

    return results


def generate_report(results: List[dict], output_dir: Path, parallel_workers: int = 1):
    """
    生成下载报告（JSON + Markdown）

    Args:
        results: 下载结果列表
        output_dir: 输出目录（默认 results/）
        parallel_workers: 并发线程数（用于报告展示）
    """
    total = len(results)
    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = total - success - skipped
    total_time = sum(r["elapsed"] for r in results)

    # 统计失败的股票代码
    failed_symbols = [r["symbol"] for r in results if r["status"] not in ("success", "skipped")]

    # 生成JSON报告（使用utils.io工具）
    json_data = {
        "total": total,
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "failed_symbols": failed_symbols,
        "duration_seconds": round(total_time, 2),
        "parallel_workers": parallel_workers,
        "details": results
    }

    json_path = output_dir / "batch_download_report.json"
    save_json_with_metadata(json_data, json_path, phase="Phase 8.2", version="1.1.0")

    # 生成Markdown报告
    md_path = output_dir / "batch_download_report.md"

    report = f"""# 批量下载报告

## 概览
- **总计**: {total} 只股票
- **成功**: {success} 只 ({success/total*100:.1f}%)
- **跳过**: {skipped} 只 ({skipped/total*100:.1f}%)
- **失败**: {failed} 只 ({failed/total*100:.1f}%)
- **总耗时**: {total_time:.1f} 秒
- **平均耗时**: {total_time/max(total-skipped, 1):.1f} 秒/只（不含跳过）
- **并发线程**: {parallel_workers} 个

## 详细结果

| 股票代码 | 状态 | 耗时 | 备注 |
|----------|------|------|------|
"""

    for r in results:
        status_map = {
            "success": "✅",
            "skipped": "⏭️",
            "failed": "❌",
            "timeout": "⏱️",
            "error": "💥"
        }
        status_emoji = status_map.get(r["status"], "❓")
        report += f"| {r['symbol']} | {status_emoji} {r['status']} | {r['elapsed']:.1f}s | {r['message'][:50]} |\n"

    if failed > 0:
        report += "\n## 失败详情\n\n"
        for r in results:
            if r["status"] not in ("success", "skipped"):
                report += f"### {r['symbol']}\n"
                report += f"```\n{r['message']}\n```\n\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)

    # 终端输出
    print(f"\n{'='*60}")
    print(f"📊 下载报告已生成")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    print(f"{'='*60}")
    print(f"成功: {success}/{total}  |  跳过: {skipped}/{total}  |  失败: {failed}/{total}")
    print(f"总耗时: {total_time:.1f}s  |  并发: {parallel_workers} 线程")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="批量下载股票数据（支持并行下载和断点续传）",
        epilog="""
示例用法：
  # 串行下载（默认）
  python scripts/batch_download.py --years 3

  # 并行下载（推荐5线程）
  python scripts/batch_download.py --years 3 --parallel 5

  # 断点续传（跳过已下载）
  python scripts/batch_download.py --years 3 --resume --parallel 5

  # 使用large_cap池（100只股票）
  python scripts/batch_download.py --pool large_cap --years 3 --parallel 5 --resume
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--years", type=int, default=3,
        help="回溯年数（默认 3 年）"
    )

    # 从配置系统获取可用池列表
    valid_pools = ['small_cap', 'medium_cap', 'large_cap', 'legacy_test_pool']

    parser.add_argument(
        "--pool", type=str, default='medium_cap',
        choices=valid_pools,
        help=f'股票池选择（可用: {", ".join(valid_pools)}）'
    )

    parser.add_argument(
        "--parallel", type=int, default=1,
        help="并发下载数（推荐3-5，默认1=串行）"
    )

    parser.add_argument(
        "--resume", action='store_true',
        help="断点续传，跳过已下载的股票（检查~/.qlib/qlib_data/cn_data/）"
    )

    args = parser.parse_args()

    # 验证并发参数
    if args.parallel < 1 or args.parallel > 10:
        print("❌ --parallel 参数范围应为 1-10")
        sys.exit(1)

    # 从配置系统加载股票池
    stocks = load_stock_pool(args.pool)

    if not stocks:
        print("❌ 股票池为空")
        sys.exit(1)

    # 显示配置信息
    print(f"\n{'='*60}")
    print(f"📋 下载配置")
    print(f"{'='*60}")
    print(f"股票池: {args.pool} ({len(stocks)} 只)")
    print(f"回溯年数: {args.years} 年")
    print(f"并发模式: {'串行' if args.parallel == 1 else f'并行 ({args.parallel} 线程)'}")
    print(f"断点续传: {'启用' if args.resume else '禁用'}")
    print(f"{'='*60}\n")

    # 执行下载（串行 or 并行）
    start_time = time.time()

    if args.parallel > 1:
        # 并行下载
        results = download_with_parallel(stocks, args.years, args.parallel, args.resume)
    else:
        # 串行下载（保留原有逻辑）
        results = []

        # 断点续传检查
        if args.resume:
            print("\n🔍 检查已下载的股票...")
            to_download = []
            skipped_count = 0

            for stock in stocks:
                symbol = stock["symbol"]
                if is_already_downloaded(symbol, min_records=500):
                    skipped_count += 1
                    results.append({
                        "symbol": symbol,
                        "status": "skipped",
                        "elapsed": 0,
                        "message": "已存在，跳过"
                    })
                else:
                    to_download.append(stock)

            print(f"✅ 已下载: {skipped_count} 只")
            print(f"📥 待下载: {len(to_download)} 只\n")

            if not to_download:
                print("\n🎉 所有股票已下载完成！")
                total_time = time.time() - start_time
                generate_report(results, Path("results"), parallel_workers=1)
                return
        else:
            to_download = stocks

        # 使用进度条（如果可用）
        iterator = tqdm(to_download, desc="下载进度", unit="只") if TQDM_AVAILABLE else to_download

        for i, stock in enumerate(iterator, 1):
            symbol = stock["symbol"]
            name = stock.get("name", "")
            sector = stock.get("sector", "")

            if not TQDM_AVAILABLE:
                print(f"\n[{i}/{len(to_download)}] {symbol} - {name} ({sector})")

            result = download_stock(symbol, args.years, silent=TQDM_AVAILABLE)
            results.append(result)

            # 避免请求过快，休息 2 秒
            if i < len(to_download):
                time.sleep(2)

    # 计算总耗时
    total_time = time.time() - start_time

    # 生成报告
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    generate_report(results, output_dir, parallel_workers=args.parallel)

    # 性能总结
    print(f"\n🏁 批量下载完成！总耗时: {total_time/60:.1f} 分钟")


if __name__ == "__main__":
    main()
