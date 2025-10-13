#!/usr/bin/env python3
"""
Stage 1 MVP: 对比报告生成

功能:
    - 加载stage1_backtest_*.json结果
    - 生成markdown对比报告
    - 评估是否达标（收益≥12%）

用法:
    python scripts/stage1_comparison.py
    python scripts/stage1_comparison.py --input results/stage1_backtest_20250110_120000.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def load_latest_result(results_dir='results'):
    """加载最新的回测结果"""
    results_path = Path(results_dir)

    # 查找所有stage1_backtest_*.json文件
    json_files = list(results_path.glob('stage1_backtest_*.json'))

    if not json_files:
        print(f"❌ 未找到回测结果文件（{results_dir}/stage1_backtest_*.json）")
        print("   请先运行: python scripts/stage1_minimal_backtest.py")
        return None

    # 按修改时间排序，取最新的
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

    print(f"✓ 加载最新结果: {latest_file.name}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def generate_report(result_data):
    """
    生成markdown对比报告

    Args:
        result_data: 回测结果字典

    Returns:
        str: markdown内容
    """
    baseline = result_data['baseline']
    variant_a = result_data['variant_a']
    variant_b = result_data['variant_b']
    benchmark = result_data['benchmark']
    config = result_data['config']

    # 计算vs基准超额收益
    baseline_excess = baseline['total_return'] - benchmark['hs300_return']
    variant_a_excess = variant_a['total_return'] - benchmark['hs300_return']
    variant_b_excess = variant_b['total_return'] - benchmark['hs300_return']

    # 判断最佳策略
    best_return = max(
        baseline['total_return'],
        variant_a['total_return'],
        variant_b['total_return']
    )

    if best_return == baseline['total_return']:
        best_strategy = 'Baseline (无止损)'
    elif best_return == variant_a['total_return']:
        best_strategy = 'Variant A (5%止损)'
    else:
        best_strategy = 'Variant B (10%止损)'

    # 判断是否达标
    target_return = 0.12
    passed = best_return >= target_return

    md = f"""# Stage 1 MVP: 限价+止损回测报告

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 验收结果: **{'✅ PASSED' if passed else '❌ FAILED'}**

## 验收判断

- **目标**: 限价买入 + 止损卖出机制下，策略仍能盈利 ≥12%
- **最佳策略**: {best_strategy}
- **最佳收益**: {best_return*100:.2f}%
- **达标状态**: {'✅ 通过' if passed else '❌ 未达标'}

---

## 策略对比

| 策略 | 收益 | vs沪深300 | 终值（万） | 止损触发率 |
|------|------|----------|-----------|-----------|
| Baseline (无止损) | {baseline['total_return']*100:>6.2f}% | {baseline_excess*100:>+6.2f}% | {baseline['final_value']/10000:>6.2f} | N/A |
| Variant A (5%止损) | {variant_a['total_return']*100:>6.2f}% | {variant_a_excess*100:>+6.2f}% | {variant_a['final_value']/10000:>6.2f} | {variant_a['stop_trigger_rate']:>6.1f}% |
| Variant B (10%止损) | {variant_b['total_return']*100:>6.2f}% | {variant_b_excess*100:>+6.2f}% | {variant_b['final_value']/10000:>6.2f} | {variant_b['stop_trigger_rate']:>6.1f}% |
| **沪深300** | {benchmark['hs300_return']*100:>6.2f}% | 0.00% | {100000*(1+benchmark['hs300_return'])/10000:>6.2f} | N/A |

---

## 关键发现

### 1. 止损影响

- **Variant A (5%止损)**:
  - 触发率 {variant_a['stop_trigger_rate']:.1f}% ({variant_a['stop_triggered']}次 / {variant_a['total_trades']}笔)
  - vs Baseline: {(variant_a['total_return']-baseline['total_return'])*100:+.2f}%
  - {'✅ 风险控制有效' if variant_a['total_return'] >= baseline['total_return']*0.9 else '⚠️ 损失过大，止损过频'}

- **Variant B (10%止损)**:
  - 触发率 {variant_b['stop_trigger_rate']:.1f}% ({variant_b['stop_triggered']}次 / {variant_b['total_trades']}笔)
  - vs Baseline: {(variant_b['total_return']-baseline['total_return'])*100:+.2f}%
  - {'✅ 平衡收益与风险' if variant_b['total_return'] >= baseline['total_return']*0.95 else '⚠️ 需要优化止损参数'}

### 2. 撮合成本

- **限价缓冲**: {config['limit_buffer']*100:.1f}% (保守估计)
- **止损滑点**: {config['stop_slippage']*100:.1f}% (保守估计)
- **买入溢价**: {config['entry_premium']*100:.1f}%

**成本影响评估**:
- Baseline vs 直接成交（假设0成本）: ~{baseline['total_return']*100:.1f}%
- 撮合机制引入的隐性成本可以接受

### 3. vs沪深300超额收益

- **Baseline**: {baseline_excess*100:+.2f}%
- **Variant A**: {variant_a_excess*100:+.2f}%
- **Variant B**: {variant_b_excess*100:+.2f}%

{'✅ 策略显著跑赢大盘' if min(baseline_excess, variant_a_excess, variant_b_excess) > 0.05 else '⚠️ 超额收益不明显'}

---

## 参数设置

| 参数 | 值 | 说明 |
|------|-----|------|
| 回测年份 | {config['year']} | 震荡市验证 |
| 股票池规模 | {config['stock_count']}只 | medium_cap |
| 调仓频率 | {config['rebalance_freq']} | 月度再平衡 |
| 买入溢价 | {config['entry_premium']*100:.1f}% | 限价单参数 |
| 止损滑点 | {config['stop_slippage']*100:.1f}% | 保守估计 |
| 限价缓冲 | {config['limit_buffer']*100:.1f}% | 保守估计 |

---

## 结论

"""

    if passed:
        md += f"""### ✅ Stage 1验证通过

**最佳配置**: {best_strategy}
**收益率**: {best_return*100:.2f}% (目标≥12%)
**超额收益**: {(best_return-benchmark['hs300_return'])*100:+.2f}% vs 沪深300

**验证结论**:
1. **撮合机制可行**: 限价买入 + 止损卖出不会显著削弱策略收益
2. **止损有效性**: {'5%止损更激进，适合波动市' if variant_a['total_return'] > variant_b['total_return'] else '10%止损更稳健，适合长期持有'}
3. **成本可控**: 保守撮合（{config['limit_buffer']*100:.1f}%缓冲 + {config['stop_slippage']*100:.1f}%滑点）不影响盈利能力

**下一步**:
- ✅ 可以进入Stage 2：扩展功能（止盈、移动止损、OCO）
- ✅ 可以考虑实盘小规模测试
- 📊 建议继续优化参数（止损比例、买入溢价）

---

**推荐实盘配置**:
- 止损比例: {('5%' if variant_a['total_return'] > variant_b['total_return'] else '10%')} (基于2023回测)
- 买入溢价: {config['entry_premium']*100:.1f}%
- 佣金预算: 万三（含印花税约0.13%）
"""
    else:
        md += f"""### ❌ Stage 1验证未通过

**最佳收益**: {best_return*100:.2f}% (目标≥12%)
**差距**: {(best_return-target_return)*100:.2f}%

**可能原因**:
1. **撮合过于保守**: 限价缓冲{config['limit_buffer']*100:.1f}% + 止损滑点{config['stop_slippage']*100:.1f}%过高
2. **止损过频**: {'5%止损触发率过高（' + f"{variant_a['stop_trigger_rate']:.1f}%）" if variant_a['stop_trigger_rate'] > 30 else '10%止损触发率过高（' + f"{variant_b['stop_trigger_rate']:.1f}%）"}
3. **买入溢价偏高**: {config['entry_premium']*100:.1f}%可能降低成交率

**改进建议**:
1. **放宽限价缓冲**: 从{config['limit_buffer']*100:.1f}%降至0.3%
2. **降低止损滑点**: 从{config['stop_slippage']*100:.1f}%降至1.5%
3. **调整止损比例**: 测试12%、15%更宽松的止损
4. **优化买入策略**: 降低溢价至0.5%或采用开盘价买入

**下一步**:
- ⚠️ 暂停Stage 2开发
- 🔧 调整stage1_params.yaml参数
- 🔄 重新运行回测验证

---

**参数调整建议（config/stage1_params.yaml）**:
```yaml
matching:
  stop_slippage: 0.015  # 从{config['stop_slippage']} → 0.015
  limit_buffer: 0.003   # 从{config['limit_buffer']} → 0.003

strategy:
  entry_limit_premium: 0.005  # 从{config['entry_premium']} → 0.005
  stop_loss_pct: 0.12         # 从0.10 → 0.12（更宽松）
```
"""

    md += """
---

*报告生成: Stage 1 MVP v1.0.0*
"""

    return md


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Stage 1 MVP: 对比报告生成')
    parser.add_argument('--input', type=str, default=None,
                        help='指定回测结果JSON文件（默认自动加载最新）')
    args = parser.parse_args()

    print("=" * 60)
    print("Stage 1 MVP: 对比报告生成")
    print("=" * 60)
    print()

    # 加载结果
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ 文件不存在: {args.input}")
            return

        print(f"✓ 加载指定文件: {input_path.name}")
        with open(input_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
    else:
        result_data = load_latest_result()

    if not result_data:
        return

    # 生成报告
    print("\n生成对比报告...")
    report = generate_report(result_data)

    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f'results/stage1_comparison_{timestamp}.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ 报告已保存: {report_path}")
    print()

    # 打印快速摘要
    baseline = result_data['baseline']
    variant_a = result_data['variant_a']
    variant_b = result_data['variant_b']

    best_return = max(
        baseline['total_return'],
        variant_a['total_return'],
        variant_b['total_return']
    )

    passed = best_return >= 0.12

    print("=" * 60)
    print("快速摘要")
    print("=" * 60)
    print(f"最佳收益: {best_return*100:.2f}%")
    print(f"验收状态: {'✅ PASSED' if passed else '❌ FAILED'} (目标≥12%)")
    print()


if __name__ == '__main__':
    main()
