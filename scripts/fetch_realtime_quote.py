#!/usr/bin/env python3
"""
实时行情获取验证脚本 - Phase 1 MVP

功能：从新浪财经获取实时行情（CLI验证用）

用法：
    python scripts/fetch_realtime_quote.py 600519.SH
    python scripts/fetch_realtime_quote.py 600519.SH 000001.SZ 601318.SH

设计原则：
- KISS：单源（新浪）最小可行版本
- DRY：复用 utils.realtime_quote 工具模块
- 透明：详细日志，便于调试

作者: Claude Code
日期: 2025-10-13
更新: 2025-10-14 (重构为导入工具模块，消除代码重复)
"""

import sys
import os
import logging

# 添加项目根目录到 sys.path（支持从任意目录运行）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入公开接口（避免依赖私有函数）
from utils.realtime_quote import fetch_sina_quote

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数：CLI入口（仅负责参数解析和格式化输出）"""
    if len(sys.argv) < 2:
        print("用法：python scripts/fetch_realtime_quote.py <股票代码1> [股票代码2] ...")
        print("示例：python scripts/fetch_realtime_quote.py 600519.SH 000001.SZ")
        sys.exit(1)

    symbols = sys.argv[1:]

    print("=" * 70)
    print("实时行情获取测试 - Phase 1 MVP (使用 utils.realtime_quote)")
    print("=" * 70)
    print(f"目标数量: {len(symbols)}")
    print(f"数据来源: 新浪财经")
    print("=" * 70)
    print()

    success_count = 0
    failure_count = 0

    for symbol in symbols:
        # 调用工具模块公开接口（单一代码源头）
        quote = fetch_sina_quote(symbol)

        if quote:
            success_count += 1
            print(f"✅ {quote['name']} ({quote['symbol']})")
            print(f"   价格: ¥{quote['price']:.2f} ({quote['change_pct']:+.2f}%)")
            print(f"   区间: ¥{quote['low']:.2f} ~ ¥{quote['high']:.2f}")
            print(f"   成交量: {quote['volume']:,} 手")
            print(f"   成交额: ¥{quote['amount']:.0f} 万元")
            print(f"   时间: {quote['timestamp']}")
            print(f"   来源: {quote['source']}")
            print()
        else:
            failure_count += 1
            print(f"❌ {symbol}: 获取失败（详见日志）")
            print()

    print("=" * 70)
    print("执行结果")
    print("=" * 70)
    print(f"✅ 成功: {success_count}/{len(symbols)}")
    print(f"❌ 失败: {failure_count}/{len(symbols)}")

    if failure_count > 0:
        print()
        print("⚠️ 失败原因可能：")
        print("   1. 股票代码无效")
        print("   2. 股票停牌")
        print("   3. 网络连接问题")
        print("   4. 新浪接口限流")

    print("=" * 70)


if __name__ == '__main__':
    main()
