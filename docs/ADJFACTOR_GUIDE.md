# 复权因子(adjfactor)计算与应用完整指南

## 📋 概述

本指南介绍如何使用AData免费数据源为现有Qlib股票数据添加复权因子(adjfactor)列,解决分红除权导致的价格不连续问题。

### 为什么需要adjfactor?

**问题**: 股票分红除权后,价格会发生跳变,导致:
- 技术指标失真(MA、动量等)
- 回测收益率不准确
- 历史PE百分位无法计算

**解决方案**: 通过adjfactor进行前复权调整,使价格连续可比:
```
adjusted_price = actual_price / adjfactor
```

> **重要说明**: adjfactor 虽名为"因子(factor)"，但在本项目中作为**前复权除数(divisor)**使用。
>
> **对账等价关系**: `adjfactor ≈ raw_close / ak_qfq_close`（同日同股）

### 复权范围
| 字段 | 是否复权 | 公式 |
|------|---------|------|
| open | ✅ 是 | `adjusted_open = open / adjfactor` |
| high | ✅ 是 | `adjusted_high = high / adjfactor` |
| low | ✅ 是 | `adjusted_low = low / adjfactor` |
| close | ✅ 是 | `adjusted_close = close / adjfactor` |
| volume | ❌ 否 | 保持原值 |
| money | ❌ 否 | 保持原值 |

## 🛠️ 工具链架构

```
1. fetch_dividend_adata.py    → 获取分红数据(AData API)
   ↓
2. calculate_adjfactor.py      → 计算复权因子
   ↓
3. verify_calculated_adjfactor.py → 验证计算正确性
   ↓
4. add_adjfactor_to_all.py     → 部署到Qlib数据
```

---

## 📦 依赖安装

### 1. 安装AData

```bash
pip install adata
```

### 2. 验证安装

```bash
python -c "import adata; print(adata.__version__)"
```

---

## 🚀 完整工作流程

### Step 1: 获取分红数据

**目的**: 从AData获取所有股票的历史分红数据

```bash
# 获取medium_cap股票池(20只)的分红数据
python scripts/fetch_dividend_adata.py --pool medium_cap

# 或指定特定股票
python scripts/fetch_dividend_adata.py --symbols "000001.SZ,600519.SH"
```

**输出**:
- `data/dividend_history.csv` - 所有股票的分红记录

**预期结果示例**:
```
✅ 加载分红数据: 156 条记录,涉及 20 只股票

📋 数据字段: 股票代码, 分红年度, 除权除息日, 每股派息(税前), 每股送股, 每股转增

📊 数据样例(前3条):
  股票代码    分红年度  除权除息日    每股派息  每股送股  每股转增
  000001.SZ   2023    2024-07-26   0.35     0       0
  600519.SH   2023    2024-06-28   21.03    0       0
  ...
```

**常见问题**:
- ❌ `ImportError: No module named 'adata'` → 运行 `pip install adata`
- ❌ `⚠️ 000XXX.SZ: 无分红数据` → 正常,该股票期间未分红

---

### Step 2: 计算复权因子

**目的**: 根据分红数据计算每个交易日的adjfactor

```bash
# 计算单只股票
python scripts/calculate_adjfactor.py --symbol 000001.SZ

# 批量计算所有股票
python scripts/calculate_adjfactor.py --all
```

**核心算法**:
```python
# 最新日期: adjfactor = 1.0
# 从后往前遍历:
#   - 除权日: adjfactor[t-1] = adjfactor[t] * (close + cash + bonus*close) / close
#   - 非除权日: adjfactor[t-1] = adjfactor[t]
```

**输出**:
- `data/with_adjfactor/{symbol}.csv` - 带adjfactor列的价格数据

**预期结果示例**:
```
📊 列名映射: {'ex_date': '除权除息日', 'cash': '每股派息(税前)', 'bonus': '每股送股', 'transfer': '每股转增'}

  处理 000001.SZ...
    ✅ 000001.SZ: 计算完成,8 个分红事件,adjfactor范围: 1.0000 ~ 1.2156

📊 数据样例(最近5天):
       date   close  adjfactor
 2024-12-27   10.12      1.0000
 2024-12-26   10.09      1.0000
 2024-12-25   10.15      1.0000
 ...
```

**验证要点**:
- ✅ 最新日期adjfactor = 1.0
- ✅ 分红事件数量与实际相符

---

### Step 3: 验证计算正确性

**目的**: 三重验证确保adjfactor计算无误

```bash
# 验证单只股票
python scripts/verify_calculated_adjfactor.py --symbol 000001.SZ

# 验证所有股票并生成报告
python scripts/verify_calculated_adjfactor.py --all
```

**三重验证机制**:

1. **价格连续性验证(核心)**: 除权日真实收益与调整后收益一致
   ```text
   设 t 为除权日前一交易日, t+1 为除权日
   真实收益(含送转和派息):
     real_return = ((1 + bonus + transfer) * close[t+1] + cash) / close[t] - 1
   调整后收益(统一使用 close / adjfactor):
     adj_close[t]   = close[t]   / adjfactor[t]
     adj_close[t+1] = close[t+1] / adjfactor[t+1]
     adj_return = adj_close[t+1] / adj_close[t] - 1
   验收: |real_return - adj_return| < 0.01
   ```

2. **adjfactor变化验证**: adjfactor只在分红日变化
   ```
   非除权日: adjfactor[t] == adjfactor[t-1]
   ```

3. **锚点验证**:
   ```
   - 最新日期 adjfactor = 1.0 ± 0.001
   - 除权锚点收益一致性: |real_return - adj_return| < 0.01
   ```

**输出**:
- `results/adjfactor_verification_report.csv` - 验证报告

**预期结果示例**:
```
  验证 000001.SZ...
    ✅ 000001.SZ: 验证通过
       分红次数: 8
       adjfactor范围: 1.0000 ~ 1.2156

验证摘要
===========================================================
总计: 20 只股票
通过: 19 只 (95.0%)
失败: 1 只 (5.0%)
===========================================================

失败股票:
  300059.SZ: 2 个问题
```

**失败处理**:

如果验证失败,检查:
1. 分红数据是否正确(AData数据质量)
2. 价格数据是否完整(Qlib数据)
3. 列名映射是否准确(calculate_adjfactor.py中的检测逻辑)

```bash
# 查看详细错误
python scripts/verify_calculated_adjfactor.py --symbol 300059.SZ

# 常见问题:
# - "除权日调整后价格跳变12.5%" → AData分红数据可能不全
# - "adjfactor在非分红日变化" → 计算逻辑bug,需调试
```

---

### Step 4: 部署到Qlib数据

**目的**: 将验证通过的adjfactor应用到生产环境

**⚠️ 重要**: 此步骤会修改Qlib原始数据,建议先模拟运行

```bash
# 1. 模拟运行(推荐)
python scripts/add_adjfactor_to_all.py --all --dry-run

# 2. 查看变更预览
python scripts/add_adjfactor_to_all.py --symbol 000001.SZ --dry-run

# 3. 实际部署(需确认)
python scripts/add_adjfactor_to_all.py --all

# 输入 yes 确认
⚠️  确认要更新所有股票吗? (yes/no): yes
```

**自动备份**:
- 原文件备份到: `~/.qlib/qlib_data/cn_data_backup/`
- 更新失败时原文件不受影响

**回滚操作**:
```bash
# 如果发现问题,一键回滚
python scripts/add_adjfactor_to_all.py --rollback

⚠️  确认要回滚所有股票到备份版本吗? (yes/no): yes
```

**预期结果**:
```
开始批量应用adjfactor...
------------------------------------------------------------

共 20 只股票需要处理

⚠️  确认要更新所有股票吗? (yes/no): yes

  处理 000001.SZ...
    💾 000001.SZ: 已备份到 ~/.qlib/qlib_data/cn_data_backup/000001.SZ.csv
    ✅ 000001.SZ: 已更新Qlib数据

  处理 600519.SH...
    💾 600519.SH: 已备份到 ~/.qlib/qlib_data/cn_data_backup/600519.SH.csv
    ✅ 600519.SH: 已更新Qlib数据

...

===========================================================
✅ 批量更新完成: 成功 20 只, 失败 0 只
===========================================================

备份位置: ~/.qlib/qlib_data/cn_data_backup
回滚命令: python scripts/add_adjfactor_to_all.py --rollback

下一步:
  1. 验证Qlib数据: ls ~/.qlib/qlib_data/cn_data/*.csv | head -3
  2. 重新运行回测: python scripts/phase6d_backtest.py --year 2023
===========================================================
```

---

## 🔍 验证部署结果

### 1. 检查CSV文件

```bash
# 查看文件是否有adjfactor列
head -2 ~/.qlib/qlib_data/cn_data/000001.SZ.csv

# 预期输出:
# date,open,high,low,close,volume,money,adjfactor
# 2020-01-02,10.09,10.12,10.05,10.10,1234567,12345678.9,1.1234
```

### 2. Python验证

```python
import pandas as pd

# 读取数据
df = pd.read_csv('~/.qlib/qlib_data/cn_data/000001.SZ.csv')

# 检查列
print(df.columns.tolist())
# 预期: ['date', 'open', 'high', 'low', 'close', 'volume', 'money', 'adjfactor']

# 检查adjfactor
print(f"adjfactor范围: {df['adjfactor'].min():.4f} ~ {df['adjfactor'].max():.4f}")
print(f"最新adjfactor: {df.iloc[-1]['adjfactor']:.4f}")  # 应为1.0000

# 计算调整后价格(除法)
df['adj_close'] = df['close'] / df['adjfactor']
df['adj_open'] = df['open'] / df['adjfactor']
df['adj_high'] = df['high'] / df['adjfactor']
df['adj_low'] = df['low'] / df['adjfactor']
# volume/money 不做复权
print(df[['date', 'close', 'adjfactor', 'adj_close']].tail(10))
```

### 3. 重新运行回测

```bash
# 使用新的adjfactor数据重新回测
python scripts/phase6d_backtest.py --year 2023

# 对比回测结果差异
# - 收益率是否更合理
# - 技术指标是否更平滑
```

---

## 📊 数据结构说明

### dividend_history.csv

```csv
symbol,name,分红年度,除权除息日,每股派息(税前),每股送股,每股转增
000001.SZ,平安银行,2023,2024-07-26,0.35,0,0
600519.SH,贵州茅台,2023,2024-06-28,21.03,0,0
```

**关键字段**:
- `除权除息日`: 股价调整发生的日期
- `每股派息(税前)`: 现金分红(元/股)
- `每股送股`: 每股送股数(股/股，已除以10)
- `每股转增`: 每股转增数(股/股，已除以10)

### with_adjfactor/{symbol}.csv

```csv
date,open,high,low,close,volume,money,adjfactor
2024-12-27,10.09,10.15,10.05,10.12,1234567,12345678.9,1.0000
2024-07-25,9.86,9.92,9.82,9.85,2345678,23456789.0,1.0356
```

**新增列**:
- `adjfactor`: 复权因子,用于计算调整后价格

**计算公式**:
```python
adjusted_close = close / adjfactor
adjusted_open = open / adjfactor
# ... 其他价格字段同理
# volume/money 不做复权
```

---

## 🐛 常见问题排查

### Q1: AData获取数据失败

```
❌ 600XXX.SH: 获取失败 - HTTP Error 500
```

**解决方案**:
1. 检查网络连接
2. 重试几次(AData可能临时不可用)
3. 检查股票代码格式:
   - 对 AData API: 使用纯数字 (如 `000001`, `600519`)
   - 对本地/Qlib/AKShare: 使用带后缀格式 (如 `000001.SZ`, `600519.SH`)

### Q2: 验证失败 - 价格跳变过大

```
❌ 300059.SZ: 验证失败
   - 除权日 2024-07-26 调整后价格跳变 12.5%
```

**可能原因**:
1. AData分红数据不全(缺少送转数据)
2. 分红日期不准确
3. 价格数据本身有问题

**解决方案**:
```bash
# 1. 手动检查分红数据
grep "300059.SZ" data/dividend_history.csv

# 2. 对比AKShare分红数据
python -c "import akshare as ak; print(ak.stock_dividend_cninfo(symbol='300059'))"

# 3. 如果确认数据正确,可调整验证阈值(verify_calculated_adjfactor.py:threshold参数)
```

### Q3: 列名映射失败

```
⚠️ 000001.SZ: 未找到除权除息日列,adjfactor全部设为1.0
```

**解决方案**:
```bash
# 1. 查看实际字段名
python scripts/fetch_dividend_adata.py --symbols "000001.SZ"
# 输出会显示: 📋 数据字段: ...

# 2. 修改calculate_adjfactor.py中的detect_dividend_columns函数
# 添加新的列名候选项
```

### Q4: 回滚后还想重新部署

```bash
# 1. 删除备份(强制重新备份)
rm -rf ~/.qlib/qlib_data/cn_data_backup

# 2. 重新部署
python scripts/add_adjfactor_to_all.py --all
```

---

## 📈 应用场景

### 场景1: 历史PE百分位计算

```python
# 现在可以计算准确的历史PE百分位
df = pd.read_csv('~/.qlib/qlib_data/cn_data/600519.SH.csv')
df['adj_close'] = df['close'] / df['adjfactor']

# 计算PE(假设已有earnings数据)
df['pe'] = df['adj_close'] / df['earnings_per_share']

# 计算历史百分位
current_pe = df.iloc[-1]['pe']
pe_percentile = (df['pe'] < current_pe).sum() / len(df) * 100
print(f"当前PE历史百分位: {pe_percentile:.1f}%")
```

### 场景2: 技术指标优化

```python
# 使用调整后价格计算MA
df['adj_close'] = df['close'] / df['adjfactor']
df['ma5'] = df['adj_close'].rolling(5).mean()
df['ma10'] = df['adj_close'].rolling(10).mean()

# 金叉信号
golden_cross = (df['ma5'] > df['ma10']) & (df['ma5'].shift(1) <= df['ma10'].shift(1))
```

### 场景3: 回测策略改进

```bash
# 重新运行Phase6d回测,使用adjfactor数据
python scripts/phase6d_backtest.py --year 2023

# 对比改进前后:
# - 收益率曲线是否更平滑
# - 夏普比率是否更高
# - 最大回撤是否减小
```

---

## 📚 相关文档

- [AData文档](https://github.com/1nchaos/adata)
- [动态复权原理](https://hopestar.github.io/stock-dynamic-rights-adjustment/)
- [Qlib数据格式](https://qlib.readthedocs.io/en/latest/component/data.html)
- [前复权vs后复权](https://baike.baidu.com/item/复权)

---

## 🎯 总结

### 完整命令序列

```bash
# 1. 获取分红数据(1-2分钟)
python scripts/fetch_dividend_adata.py --pool medium_cap

# 2. 计算adjfactor(30秒)
python scripts/calculate_adjfactor.py --all

# 3. 验证正确性(30秒)
python scripts/verify_calculated_adjfactor.py --all

# 4. 模拟部署(10秒)
python scripts/add_adjfactor_to_all.py --all --dry-run

# 5. 实际部署(30秒)
python scripts/add_adjfactor_to_all.py --all

# 6. 验证结果(10秒)
head -2 ~/.qlib/qlib_data/cn_data/000001.SZ.csv

# 7. 重新回测(5-10分钟)
python scripts/phase6d_backtest.py --year 2023
```

### 时间估算

- **首次完整流程**: 约15-20分钟
- **后续增量更新**: 约5分钟(只更新新分红数据)

### 注意事项

1. ✅ **备份重要**: 首次运行前确保重要数据已备份
2. ✅ **网络依赖**: 仅fetch_dividend_adata需要网络,其他脚本离线可用
3. ✅ **验证必须**: 不要跳过verify步骤,确保数据质量
4. ✅ **增量更新**: 定期(如每季度)重新获取分红数据并更新

---

**文档版本**: v1.2
**最后更新**: 2025-12-16
**维护者**: Stock Project Team
