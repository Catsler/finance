#!/usr/bin/env python3
"""
批量下载股票数据脚本

用法：
    python scripts/batch_download.py --years 3

功能：
    - 从 stock_pool.yaml 读取股票列表
    - 批量调用 akshare-to-qlib-converter.py 下载数据
    - 生成下载报告
"""

import argparse
import subprocess
import time
from pathlib import Path
import sys

# 添加 scripts 目录到路径，以便导入转换脚本
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ruamel.yaml import YAML
except ImportError:
    print("请安装 ruamel.yaml: pip install ruamel.yaml")
    sys.exit(1)


def load_stock_pool(yaml_path: Path, pool_name: str = 'medium_cap') -> list:
    """
    从 YAML 文件加载股票池
    
    Args:
        yaml_path: YAML配置文件路径
        pool_name: 股票池名称（small_cap/medium_cap）
    
    Returns:
        list: 股票列表
    """
    yaml = YAML(typ="safe")
    with open(yaml_path) as f:
        config = yaml.load(f)

    stock_pools = config.get('stock_pools', {})
    
    if pool_name == 'small_cap':
        # 直接返回small_cap列表
        stocks = stock_pools.get('small_cap', [])
    elif pool_name == 'medium_cap':
        # medium_cap = small_cap + additional
        small_cap_stocks = stock_pools.get('small_cap', [])
        medium_cap_config = stock_pools.get('medium_cap', {})
        additional_stocks = medium_cap_config.get('additional', [])
        stocks = small_cap_stocks + additional_stocks
    else:
        print(f"❌ 未知股票池: {pool_name}")
        sys.exit(1)
    
    print(f"✅ 加载 {pool_name}（{len(stocks)} 只股票）")
    return stocks


def download_stock(symbol: str, years: int) -> dict:
    """下载单只股票数据"""
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
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {symbol} 下载成功 (耗时 {elapsed:.1f}s)")
            return {
                "symbol": symbol,
                "status": "success",
                "elapsed": elapsed,
                "message": "下载成功"
            }
        else:
            print(f"❌ {symbol} 下载失败")
            print(f"错误: {result.stderr}")
            return {
                "symbol": symbol,
                "status": "failed",
                "elapsed": elapsed,
                "message": result.stderr.strip()
            }

    except subprocess.TimeoutExpired:
        print(f"❌ {symbol} 下载超时 (>120s)")
        return {
            "symbol": symbol,
            "status": "timeout",
            "elapsed": 120,
            "message": "下载超时"
        }
    except Exception as e:
        print(f"❌ {symbol} 下载出错: {e}")
        return {
            "symbol": symbol,
            "status": "error",
            "elapsed": 0,
            "message": str(e)
        }


def generate_report(results: list, output_path: Path):
    """生成下载报告"""
    total = len(results)
    success = sum(1 for r in results if r["status"] == "success")
    failed = total - success
    total_time = sum(r["elapsed"] for r in results)

    report = f"""# 批量下载报告

## 概览
- **总计**: {total} 只股票
- **成功**: {success} 只 ({success/total*100:.1f}%)
- **失败**: {failed} 只 ({failed/total*100:.1f}%)
- **总耗时**: {total_time:.1f} 秒
- **平均耗时**: {total_time/total:.1f} 秒/只

## 详细结果

| 股票代码 | 状态 | 耗时 | 备注 |
|----------|------|------|------|
"""

    for r in results:
        status_emoji = "✅" if r["status"] == "success" else "❌"
        report += f"| {r['symbol']} | {status_emoji} {r['status']} | {r['elapsed']:.1f}s | {r['message'][:50]} |\n"

    if failed > 0:
        report += "\n## 失败详情\n\n"
        for r in results:
            if r["status"] != "success":
                report += f"### {r['symbol']}\n"
                report += f"```\n{r['message']}\n```\n\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"📊 下载报告已生成: {output_path}")
    print(f"{'='*60}")
    print(f"成功: {success}/{total}  |  失败: {failed}/{total}  |  总耗时: {total_time:.1f}s")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="批量下载股票数据")
    parser.add_argument(
        "--years", type=int, default=3, help="回溯年数（默认 3 年）"
    )
    parser.add_argument(
        "--config", default="stock_pool.yaml", help="股票池配置文件路径（默认stock_pool.yaml）"
    )
    parser.add_argument(
        "--pool", type=str, default='medium_cap',
        choices=['small_cap', 'medium_cap'],
        help='股票池（默认medium_cap=20只[推荐], small_cap=10只[legacy]）'
    )
    args = parser.parse_args()

    # 加载股票池
    pool_path = Path(args.config)
    if not pool_path.exists():
        print(f"❌ 股票池文件不存在: {pool_path}")
        sys.exit(1)

    stocks = load_stock_pool(pool_path, args.pool)

    if not stocks:
        print("❌ 股票池为空")
        sys.exit(1)

    print(f"\n🚀 开始批量下载 {len(stocks)} 只股票的 {args.years} 年数据...\n")

    # 批量下载
    results = []
    for i, stock in enumerate(stocks, 1):
        symbol = stock["symbol"]
        name = stock.get("name", "")
        sector = stock.get("sector", "")

        print(f"\n[{i}/{len(stocks)}] {symbol} - {name} ({sector})")

        result = download_stock(symbol, args.years)
        results.append(result)

        # 避免请求过快，休息 2 秒
        if i < len(stocks):
            time.sleep(2)

    # 生成报告
    report_path = Path("batch_download_report.md")
    generate_report(results, report_path)


if __name__ == "__main__":
    main()
