#!/usr/bin/env python3
"""
价格修复验证脚本

验证点：
1. CSV 文件中的价格是否为真实价格（非后复权）
2. Backend 读取价格是否正确
3. 预算利用率是否提升至 80-100%
"""

import sys
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.portfolio_manager import VirtualPortfolio
import pandas as pd

def verify_csv_prices():
    """验证 CSV 文件中的价格"""
    print("=" * 60)
    print("1️⃣  验证 CSV 文件价格（真实交易价格）")
    print("=" * 60)

    qlib_data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"

    test_stocks = [
        ("000001.SZ", "平安银行", (8, 20)),     # 预期价格范围
        ("600519.SH", "贵州茅台", (1200, 1600)),
        ("300750.SZ", "宁德时代", (300, 500)),
        ("002594.SZ", "比亚迪", (90, 150)),
        ("600900.SH", "长江电力", (20, 35)),
    ]

    all_passed = True

    for symbol, name, (min_price, max_price) in test_stocks:
        csv_file = qlib_data_dir / f"{symbol}.csv"

        if not csv_file.exists():
            print(f"❌ {symbol} ({name}): 数据文件不存在")
            all_passed = False
            continue

        df = pd.read_csv(csv_file)
        latest_close = df.iloc[-1]['close']

        if min_price <= latest_close <= max_price:
            print(f"✅ {symbol} ({name}): ¥{latest_close:.2f} - 价格正常（真实价格）")
        else:
            print(f"⚠️  {symbol} ({name}): ¥{latest_close:.2f} - 价格异常（预期 ¥{min_price}-{max_price}）")
            all_passed = False

    print()
    return all_passed

def verify_backend_prices():
    """验证 Backend 读取价格"""
    print("=" * 60)
    print("2️⃣  验证 Backend 价格读取")
    print("=" * 60)

    pm = VirtualPortfolio()

    test_stocks = [
        "000001.SZ",  # 平安银行
        "600519.SH",  # 贵州茅台
        "300750.SZ",  # 宁德时代
    ]

    all_passed = True

    for symbol in test_stocks:
        price = pm._get_current_price(symbol)

        if price is None:
            print(f"❌ {symbol}: 无法读取价格")
            all_passed = False
        elif price < 5:
            print(f"⚠️  {symbol}: ¥{price:.2f} - 价格过低（可能数据问题）")
            all_passed = False
        elif price > 10000:
            print(f"❌ {symbol}: ¥{price:.2f} - 价格过高（疑似后复权价格）")
            all_passed = False
        else:
            print(f"✅ {symbol}: ¥{price:.2f}")

    print()
    return all_passed

def verify_budget_utilization():
    """验证预算利用率"""
    print("=" * 60)
    print("3️⃣  验证预算利用率（模拟选股场景）")
    print("=" * 60)

    pm = VirtualPortfolio()
    budget = 100000  # 10万预算

    # 模拟5只股票的选股结果
    test_selection = [
        {"symbol": "000001.SZ", "name": "平安银行"},
        {"symbol": "600036.SH", "name": "招商银行"},
        {"symbol": "600900.SH", "name": "长江电力"},
        {"symbol": "000858.SZ", "name": "五粮液"},
        {"symbol": "002920.SZ", "name": "德赛西威"},
    ]

    total_cost = 0
    successful_stocks = 0

    print(f"预算: ¥{budget:,.0f}\n")

    for stock in test_selection:
        symbol = stock["symbol"]
        name = stock["name"]
        price = pm._get_current_price(symbol)

        if price is None:
            print(f"⚠️  {symbol} ({name}): 无法获取价格")
            continue

        # 等权分配
        allocation = budget / len(test_selection)
        shares = int(allocation / (price * 100)) * 100  # 100股为一手
        cost = shares * price

        if shares >= 100:  # 至少能买1手
            total_cost += cost
            successful_stocks += 1
            print(f"✅ {symbol} ({name}): ¥{price:.2f} × {shares}股 = ¥{cost:,.2f}")
        else:
            print(f"❌ {symbol} ({name}): ¥{price:.2f} - 资金不足（需 ¥{price*100:.2f}/手）")

    utilization = (total_cost / budget) * 100

    print(f"\n{'─' * 60}")
    print(f"总成本: ¥{total_cost:,.2f}")
    print(f"预算利用率: {utilization:.1f}%")
    print(f"成功买入: {successful_stocks}/{len(test_selection)} 只股票")
    print(f"{'─' * 60}\n")

    # 判断是否通过
    if utilization >= 60 and successful_stocks >= 4:
        print("✅ 预算利用率测试通过（≥60% 且能买入 ≥4 只股票）")
        return True
    else:
        print(f"❌ 预算利用率测试失败（利用率 {utilization:.1f}%，买入 {successful_stocks} 只）")
        return False

def main():
    print("\n" + "=" * 60)
    print("🔍 价格修复验证程序")
    print("=" * 60)
    print()

    # 执行三项验证
    test1 = verify_csv_prices()
    test2 = verify_backend_prices()
    test3 = verify_budget_utilization()

    # 最终结论
    print("=" * 60)
    print("📊 验证结果总结")
    print("=" * 60)
    print(f"CSV 价格验证: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"Backend 读取验证: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"预算利用率验证: {'✅ 通过' if test3 else '❌ 失败'}")
    print("=" * 60)

    if test1 and test2 and test3:
        print("\n🎉 全部测试通过！价格修复成功！\n")
        print("下一步：")
        print("  1. 启动 Streamlit UI: ./run_streamlit.sh")
        print("  2. 执行选股测试预算利用率")
        print("  3. 验证价格与交易软件一致")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
