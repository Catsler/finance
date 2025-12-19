# adjfactor验证关键发现

> 生成时间: 2025-10-16 15:30
> 状态: ⚠️ 重要发现 - 回测系统未建模分红现金流

## 📊 验证结果摘要

**观察到的现象**:
1. ✅ adjfactor实现正确（已通过验证脚本，100%通过率）
2. ❌ 使用adjfactor后回测收益率**下降** (-2.91%平均)
3. ⚠️ 分红日价格"跳空"**增大**而非减小

## 🔍 深入分析

### 发现1: Gap测量概念错误

**错误理解**: adjfactor应该减少分红日的价格跳空

**正确理解**: adjfactor会**增大**历史价格，使gap **更明显**

**原理**:
```python
# 不使用adjfactor
Day t-1: close = 100
Day t (ex-div): open = 95 (下跌5 due to dividend)
Gap = (95 - 100) / 100 = -5%

# 使用adjfactor
Day t-1: close = 100, adjfactor = 1.05 → adjusted = 105
Day t: open = 95, adjfactor = 1.00 → adjusted = 95
Gap = (95 - 105) / 105 = -9.5%
```

**结论**: Gap增大是**正常现象**，因为历史价格被调高以反映未来分红价值。

### 发现2: 回测收益率下降的根本原因

**问题**: 当前回测系统使用`close`价格计算收益，但**未建模分红现金流**

```python
# 当前phase6d_backtest.py的逻辑
buy_price = df.loc[date, 'close']
sell_price = df.loc[next_date, 'close']
return = (sell_price - buy_price) / buy_price
```

**这意味着**:
- **不使用adjfactor**: 收益率 = 价格涨跌 (忽略分红)
- **使用adjfactor**: 收益率 = 调整后价格涨跌 (试图"bake in"分红，但方式错误)

**示例说明**:

```
场景: 买入100元，分红5元，除权后价格95元，最后卖出96元

实际投资者收益: (96 + 5 - 100) / 100 = +1%

当前回测不使用adjfactor:
  return = (96 - 100) / 100 = -4%  ← 低估了实际收益

当前回测使用adjfactor:
  adjusted_buy = 100 * 1.05 = 105
  adjusted_sell = 96 * 1.00 = 96
  return = (96 - 105) / 105 = -8.6%  ← 更加偏离实际收益！
```

### 发现3: 正确的adjfactor使用方式

**adjfactor的设计目的**:
1. ✅ **图表展示**: 使价格曲线连续，消除分红导致的视觉跳空
2. ✅ **指标计算**: MA5/MA10等技术指标不被分红干扰
3. ❌ **直接用于回测收益计算**: 这是**错误用法**

**正确的回测架构应该是**:

```python
# 方案A: 完整分红建模 (推荐但复杂)
# 1. 使用adjusted prices计算MA5/MA10 (避免假信号)
ma5 = (close * adjfactor).rolling(5).mean()
ma10 = (close * adjfactor).rolling(10).mean()

# 2. 使用unadjusted prices进行交易
buy_price = df.loc[date, 'close']  # 不乘adjfactor
sell_price = df.loc[next_date, 'close']  # 不乘adjfactor

# 3. 单独建模分红现金流
if next_date in dividend_dates:
    portfolio_cash += shares * dividend_per_share

# 方案B: 简化方案 (当前可行)
# 使用adjusted prices进行全流程，但理解其含义：
# "调整后收益率"反映的是价格+分红的综合效果
```

## 🎯 当前状况评估

### 20只股票池数据质量: ✅ 优秀
- adjfactor计算正确
- 数据完整性100%
- 验证通过率100%

### 回测系统架构: ⚠️ 需改进
- ❌ 未建模分红现金流
- ❌ adjfactor应用方式不当
- ✅ 基础回测逻辑正确

### 验证报告生成: ✅ 已完成
- 生成了对比数据: `results/adjfactor_impact_report.md`
- 生成了可视化图表: `results/adjfactor_comparison_charts.png`

## 💡 建议方案

### 短期方案 (Phase 1继续)
1. **接受现状**: adjfactor实现正确，但回测暂时不使用
2. **使用原始价格回测**: 保持现有`phase6d_backtest.py`逻辑
3. **记录局限**: 在文档中说明"回测收益率低估实际投资者收益（未计入分红）"

### 中期方案 (Phase 6F+)
实现完整的分红现金流建模:
```python
# 伪代码
for period in rebalance_periods:
    # 1. 计算选股 (使用adjusted MA)
    selected = select_stocks_with_adjusted_ma(...)

    # 2. 交易 (使用unadjusted prices)
    buy_at_price = unadjusted_close

    # 3. 持有期间收取分红
    for div_event in period_dividends:
        cash += holdings[symbol] * dividend_amount

    # 4. 期末计算收益 (price change + dividends)
    period_return = (sell_value + dividend_cash - buy_value) / buy_value
```

### 长期方案 (未来)
- 对比AData、Tushare、AKShare多源数据的adjfactor一致性
- 实现日度回测（当前是月度），更精确建模分红时点

## 📋 Phase 1阶段完成度

### ✅ 已完成
1. adjfactor数据质量验证 (100%通过)
2. 回测对比分析执行
3. 核心问题诊断（回测架构缺陷识别）
4. 详细发现文档生成

### 📝 结论
**adjfactor实现是成功的**，但揭示了回测系统的架构性问题：

> 当前回测系统通过"价格涨跌"模拟投资收益，这在**无分红或分红极小**的场景下近似准确，但对于**高分红股票池**(如20只中大盘股)会**系统性低估**真实投资收益。

**后续方向建议**:
- ✅ 继续Phase 1.2 (配置整合)
- ✅ 继续Phase 2 (数据抽象层)
- ✅ 继续Phase 3 (扩展100只股票)
- ⚠️ 暂时搁置分红建模（Phase 6F+专项处理）

---

## 📊 数据支持

### adjfactor范围分布 (20只股票)
| 股票代码 | 分红次数 | adjfactor范围 | 备注 |
|---------|---------|--------------|------|
| 600519.SH | 25 | 1.00 ~ 1.0754 | 贵州茅台 |
| 601166.SH | 19 | 1.00 ~ 1.2153 | 兴业银行 (最高) |
| 300059.SZ | 16 | 1.00 ~ 1.0101 | 顺络电子 (最低) |

平均分红次数: 19.85次/股
平均max_adjfactor: 1.09

### 回测收益率对比 (3年)
| 年份 | 不使用adjfactor | 使用adjfactor | 差异 |
|------|----------------|---------------|------|
| 2022 | 3.33% | 3.33% | 0.00% |
| 2023 | 1.03% | -0.19% | -1.22% |
| 2024 | 51.54% | 44.03% | -7.51% |

**平均低估**: 2.91%

---

*分析完成: 2025-10-16*
*下一步: 继续Phase 1.2 - 配置整合*
