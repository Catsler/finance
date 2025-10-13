#!/usr/bin/env python3
"""
虚拟模拟盘系统 - 跟踪实时持仓和收益

用法:
    # 初始化建仓
    python scripts/virtual_portfolio.py init --capital 1000000

    # 每日更新市值
    python scripts/virtual_portfolio.py update

    # 调仓操作
    python scripts/virtual_portfolio.py rebalance --selection results/latest_selection_20251009.json

    # 查看持仓
    python scripts/virtual_portfolio.py show
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# 导入工具
sys.path.append(str(Path(__file__).parent.parent))


def create_portfolios_dir():
    """确保portfolios目录存在"""
    port_dir = Path("portfolios")
    port_dir.mkdir(exist_ok=True)
    return port_dir


def load_latest_portfolio():
    """加载最新的持仓文件"""
    port_dir = Path("portfolios")
    if not port_dir.exists():
        return None, None

    # 查找最新的portfolio文件
    port_files = sorted(port_dir.glob("port_*.json"))
    if not port_files:
        return None, None

    latest_file = port_files[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        portfolio = json.load(f)

    return portfolio, latest_file


def get_latest_prices(symbols):
    """
    获取股票最新价格

    Args:
        symbols: 股票代码列表

    Returns:
        dict: {symbol: {"date": "YYYY-MM-DD", "price": float}}
    """
    data_dir = Path.home() / ".qlib/qlib_data/cn_data"
    prices = {}

    for symbol in symbols:
        csv_path = data_dir / f"{symbol}.csv"
        if not csv_path.exists():
            print(f"⚠️ 数据文件不存在: {csv_path}")
            continue

        df = pd.read_csv(csv_path, parse_dates=["date"], index_col="date")
        df = df.sort_index()

        if df.empty:
            print(f"⚠️ {symbol} 数据为空")
            continue

        latest_date = df.index[-1]
        latest_price = df.iloc[-1]["close"]

        prices[symbol] = {
            "date": latest_date.strftime("%Y-%m-%d"),
            "price": float(latest_price)
        }

    return prices


def init_portfolio(capital, selection_file=None):
    """
    初始化建仓

    Args:
        capital: 初始资金
        selection_file: 选股结果JSON文件路径
    """
    print("\n" + "="*60)
    print("初始化模拟盘")
    print("="*60)

    # 加载选股结果
    if selection_file:
        with open(selection_file, "r", encoding="utf-8") as f:
            selection = json.load(f)
        selected_stocks = selection["selected_stocks"]
        selection_date = selection["selection_date"]
        details = selection["details"]
    else:
        # 如果没有提供选股文件，尝试加载最新的
        results_dir = Path("results")
        selection_files = sorted(results_dir.glob("latest_selection_*.json"))
        if not selection_files:
            print("❌ 未找到选股结果文件，请先运行 select_latest.py 或指定 --selection 参数")
            sys.exit(1)

        latest_selection = selection_files[-1]
        print(f"✓ 使用最新选股结果: {latest_selection}")

        with open(latest_selection, "r", encoding="utf-8") as f:
            selection = json.load(f)
        selected_stocks = selection["selected_stocks"]
        selection_date = selection["selection_date"]
        details = selection["details"]

    if not selected_stocks:
        print("❌ 选股结果为空，无法建仓")
        sys.exit(1)

    print(f"✓ 选股日期: {selection_date}")
    print(f"✓ 选中股票: {len(selected_stocks)} 只")
    print(f"✓ 初始资金: {capital:,.2f} 元")

    # 等权分配
    capital_per_stock = capital / len(selected_stocks)
    print(f"✓ 每只股票分配: {capital_per_stock:,.2f} 元")

    # 建仓
    holdings = {}
    total_cost = 0

    print("\n持仓明细:")
    print("-" * 60)

    for symbol in selected_stocks:
        stock_detail = details[symbol]
        price = stock_detail["close"]
        name = stock_detail["name"]

        shares = int(capital_per_stock / price)
        cost = shares * price

        holdings[symbol] = {
            "name": name,
            "shares": shares,
            "avg_price": price,
            "cost": cost,
            "buy_date": selection_date
        }

        total_cost += cost
        print(f"{symbol} {name:8s} | 数量:{shares:>6d} | 成本:{price:>8.2f} | 金额:{cost:>12,.2f}")

    cash = capital - total_cost

    print("-" * 60)
    print(f"总成本: {total_cost:,.2f} 元")
    print(f"剩余现金: {cash:,.2f} 元")
    print(f"资金使用率: {total_cost/capital*100:.2f}%")

    # 构建portfolio对象
    portfolio_id = f"port_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    portfolio = {
        "portfolio_id": portfolio_id,
        "init_date": selection_date,
        "init_capital": capital,
        "holdings": holdings,
        "cash": cash,
        "history": [{
            "date": selection_date,
            "market_value": total_cost,
            "total_value": capital,
            "return_rate": 0.0,
            "cash": cash
        }],
        "trades": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 保存
    port_dir = create_portfolios_dir()
    port_file = port_dir / f"{portfolio_id}.json"

    with open(port_file, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 模拟盘已创建: {port_file}")
    print("="*60)

    return portfolio


def update_portfolio():
    """更新模拟盘市值"""
    print("\n" + "="*60)
    print("更新模拟盘")
    print("="*60)

    # 加载最新portfolio
    portfolio, port_file = load_latest_portfolio()
    if not portfolio:
        print("❌ 未找到持仓文件，请先运行 init 命令")
        sys.exit(1)

    print(f"✓ 加载持仓: {port_file.name}")
    print(f"✓ 建仓日期: {portfolio['init_date']}")
    print(f"✓ 持仓数量: {len(portfolio['holdings'])} 只")

    # 获取最新价格
    symbols = list(portfolio["holdings"].keys())
    latest_prices = get_latest_prices(symbols)

    if not latest_prices:
        print("❌ 未能获取任何最新价格")
        sys.exit(1)

    # 统一使用最新的共同日期
    latest_date = max(p["date"] for p in latest_prices.values())
    print(f"✓ 更新日期: {latest_date}")

    # 计算当前市值
    market_value = 0
    print("\n持仓状态:")
    print("-" * 80)
    print(f"{'代码':<12} {'名称':<8} {'数量':>6} {'成本':>8} {'现价':>8} {'市值':>12} {'盈亏':>10} {'收益率':>8}")
    print("-" * 80)

    for symbol, holding in portfolio["holdings"].items():
        if symbol not in latest_prices:
            print(f"⚠️ {symbol} 无最新价格，跳过")
            continue

        current_price = latest_prices[symbol]["price"]
        shares = holding["shares"]
        cost = holding["cost"]
        avg_price = holding["avg_price"]

        current_value = shares * current_price
        pnl = current_value - cost
        pnl_rate = pnl / cost if cost > 0 else 0

        market_value += current_value

        pnl_str = f"+{pnl:,.2f}" if pnl >= 0 else f"{pnl:,.2f}"
        pnl_rate_str = f"+{pnl_rate*100:.2f}%" if pnl >= 0 else f"{pnl_rate*100:.2f}%"

        print(f"{symbol:<12} {holding['name']:<8} {shares:>6d} {avg_price:>8.2f} {current_price:>8.2f} {current_value:>12,.2f} {pnl_str:>10} {pnl_rate_str:>8}")

    total_value = market_value + portfolio["cash"]
    total_return = (total_value - portfolio["init_capital"]) / portfolio["init_capital"]

    print("-" * 80)
    print(f"市值合计: {market_value:,.2f} 元")
    print(f"现金余额: {portfolio['cash']:,.2f} 元")
    print(f"总资产: {total_value:,.2f} 元")
    print(f"总收益: {(total_value - portfolio['init_capital']):+,.2f} 元 ({total_return*100:+.2f}%)")
    print("="*60)

    # 更新history
    portfolio["history"].append({
        "date": latest_date,
        "market_value": market_value,
        "total_value": total_value,
        "return_rate": total_return,
        "cash": portfolio["cash"]
    })

    # 保存
    with open(port_file, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

    print(f"✓ 持仓已更新: {port_file}")

    # 导出history CSV
    history_csv = port_file.with_suffix(".csv")
    history_df = pd.DataFrame(portfolio["history"])
    history_df.to_csv(history_csv, index=False, encoding="utf-8")
    print(f"✓ 历史记录已导出: {history_csv}")


def show_portfolio():
    """显示当前持仓"""
    portfolio, port_file = load_latest_portfolio()
    if not portfolio:
        print("❌ 未找到持仓文件")
        sys.exit(1)

    print("\n" + "="*60)
    print(f"模拟盘: {portfolio['portfolio_id']}")
    print("="*60)
    print(f"建仓日期: {portfolio['init_date']}")
    print(f"初始资金: {portfolio['init_capital']:,.2f} 元")
    print(f"持仓数量: {len(portfolio['holdings'])} 只")
    print(f"现金余额: {portfolio['cash']:,.2f} 元")

    if portfolio["history"]:
        latest = portfolio["history"][-1]
        print(f"\n最新更新: {latest['date']}")
        print(f"总资产: {latest['total_value']:,.2f} 元")
        print(f"总收益率: {latest['return_rate']*100:+.2f}%")

    print("\n持仓明细:")
    print("-" * 60)
    for symbol, holding in portfolio["holdings"].items():
        print(f"{symbol} {holding['name']:8s} | {holding['shares']:>6d}股 @ {holding['avg_price']:.2f} = {holding['cost']:,.2f}元")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="虚拟模拟盘系统")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init命令
    init_parser = subparsers.add_parser("init", help="初始化建仓")
    init_parser.add_argument("--capital", type=float, default=1000000, help="初始资金（默认100万）")
    init_parser.add_argument("--selection", help="选股结果JSON文件路径")

    # update命令
    update_parser = subparsers.add_parser("update", help="更新持仓市值")

    # show命令
    show_parser = subparsers.add_parser("show", help="显示当前持仓")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        init_portfolio(args.capital, args.selection)
    elif args.command == "update":
        update_portfolio()
    elif args.command == "show":
        show_portfolio()


if __name__ == "__main__":
    main()
