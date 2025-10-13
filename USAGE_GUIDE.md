# 📘 使用指南 - 模拟盘收益与策略验证

**快速上手指南**：如何使用现有功能查看模拟盘收益和验证选股策略

---

## 💼 Part 1: 如何查看模拟盘收益

### 1️⃣ 启动 Streamlit UI

```bash
# 方法1：使用启动脚本（推荐）
./run_streamlit.sh

# 方法2：手动启动
source venv/bin/activate
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`

### 2️⃣ 查看收益指标

访问 **💼 模拟盘** 页面，可以查看：

#### 📊 核心收益指标（页面顶部）

| 指标 | 说明 | 位置 |
|------|------|------|
| 📈 未实现盈亏 | 当前持仓的账面浮盈浮亏（未卖出） | 指标卡片1 |
| 💰 已实现盈亏 | 已平仓交易的实际收益（已卖出） | 指标卡片2 |
| 📊 总收益率 | (未实现盈亏 + 已实现盈亏) / 初始资金 | 指标卡片3 |
| 🎯 胜率 | 盈利交易数 / 总交易数 | 指标卡片4 |

#### 📦 持仓明细（Tab 1）

查看每只股票的详细收益：

```
股票代码 | 股票名称 | 持有股数 | 成本价 | 当前价 | 市值 | 盈亏 | 收益率
```

**操作**：
- 点击 **📥 下载持仓明细CSV** 导出Excel分析
- 查看持仓分布饼图（资金占比）

#### 🔄 交易历史（Tab 3）

查看所有买入/卖出记录：

```
日期 | 股票代码 | 交易类型 | 数量 | 价格 | 金额 | 备注
```

**操作**：
- 点击 **📥 下载交易历史CSV** 导出完整记录
- 按日期筛选交易

### 3️⃣ 执行再平衡（月度操作）

在 **💼 模拟盘** 页面：

1. 确认最新选股结果已生成（在 **📊 每日选股** 页面执行选股）
2. 点击 **🔄 执行再平衡** 按钮
3. 系统自动：
   - 卖出所有旧持仓（按当前价）
   - 买入最新选股结果（等权分配）
   - 记录所有交易到日志

**数据存储位置**：
- 持仓状态: `data/portfolio/virtual.json`
- 交易日志: `data/portfolio/trades.jsonl`

---

## 🔍 Part 2: 如何验证选股策略（历史回测）

### 1️⃣ 运行完整三年回测（2022-2024）

```bash
# 完整回测：2022熊市 + 2023震荡 + 2024牛转
python scripts/phase6d_backtest.py --full
```

**终端输出示例**：
```
=== 2022年回测 ===
总收益: -17.52%
年化收益: -17.52%
换手率: 68.8%
超额收益 vs 沪深300: +4.10%

=== 2023年回测 ===
总收益: +19.90%
年化收益: +19.90%
换手率: 71.2%
超额收益 vs 沪深300: +31.65%

=== 2024年回测 ===
总收益: -36.25%
年化收益: -36.25%
换手率: 65.3%
超额收益 vs 沪深300: -22.09%
```

### 2️⃣ 查看生成报告

回测完成后，自动生成以下文件：

| 文件 | 说明 | 位置 |
|------|------|------|
| `phase6d_comparison_YYYYMMDD_HHMMSS.md` | 详细对比报告（策略 vs 基准 vs 固定持仓） | results/ |
| `phase6d_judgment_YYYYMMDD_HHMMSS.json` | 验证结果JSON（是否通过红线检查） | results/ |
| `phase6d_*_holdings.csv` | 每次调仓的持仓明细 | results/ |

**查看方式**：
```bash
# 查看最新报告
ls -lt results/phase6d_comparison_*.md | head -1 | awk '{print $NF}' | xargs cat

# 或直接在文件浏览器打开 results/ 目录
```

### 3️⃣ 单年回测（快速验证）

```bash
# 只测试2023年
python scripts/phase6d_backtest.py --year 2023

# 只测试2024年
python scripts/phase6d_backtest.py --year 2024
```

### 4️⃣ 调整参数测试（策略优化）

```bash
# 放宽动量阈值（允许涨幅 >= -5%）
python scripts/phase6d_backtest.py --full --momentum-threshold -5.0

# 改为季度调仓（降低换手率）
python scripts/phase6d_backtest.py --full --rebalance-freq quarterly

# 测试不同佣金率（敏感性分析）
python scripts/phase6d_backtest.py --full --commission 0.001  # 0.1%
python scripts/phase6d_backtest.py --full --commission 0.002  # 0.2%

# 10股小池子（Legacy测试）
python scripts/phase6d_backtest.py --full --pool small_cap
```

### 5️⃣ 查看历史验证结论

**方式1：阅读总结报告**
```bash
cat PHASE8_SUMMARY.md
```

**关键结论**（第7节"策略适用边界"）：
- ✅ **熊市+震荡市有效**：2022-2023 超额收益 +19.90%
- ❌ **牛市失效**：2024年 跑输基准 -22.09%
- ⚠️ **适用场景**：市场整体低迷或震荡时，动量策略筛选强势股
- ⚠️ **不适用场景**：全面牛市时，轮动过快导致踏空主升浪

**方式2：查看项目总结**
```bash
cat PROJECT_FINAL_SUMMARY.md
```

包含Phase 0-8的完整演进历史和关键决策。

---

## ⚡ Part 3: 快速参考表

### 常见需求 → 操作映射

| 你想做什么 | 操作方式 | 结果文件/位置 |
|-----------|---------|--------------|
| **查看当前持仓收益** | Streamlit UI → 💼 模拟盘 → 持仓明细 | data/portfolio/virtual.json |
| **查看历史交易记录** | Streamlit UI → 💼 模拟盘 → 交易历史 | data/portfolio/trades.jsonl |
| **执行月度调仓** | Streamlit UI → 💼 模拟盘 → 🔄 执行再平衡 | 自动更新 virtual.json + trades.jsonl |
| **导出持仓Excel** | 点击 "📥 下载持仓明细CSV" | 浏览器下载 |
| **运行历史回测** | `python scripts/phase6d_backtest.py --full` | results/phase6d_comparison_*.md |
| **查看策略结论** | `cat PHASE8_SUMMARY.md` | 终端显示 |
| **测试不同参数** | 添加 `--momentum-threshold` 等参数 | 终端输出 + results/ |
| **查看价格数据** | 查看CSV文件 | ~/.qlib/qlib_data/cn_data/*.csv |
| **查看股票池配置** | `cat stock_pool.yaml` | 终端显示（20只股票） |

### 关键命令速查

```bash
# === UI 相关 ===
streamlit run app.py              # 启动Web界面

# === 回测相关 ===
python scripts/phase6d_backtest.py --full                    # 完整三年回测
python scripts/phase6d_backtest.py --year 2023               # 单年回测
python scripts/phase6d_backtest.py --full --commission 0.001 # 测试佣金影响
python scripts/phase6d_backtest.py --full --rebalance-freq quarterly # 季度调仓

# === 数据相关 ===
python scripts/check_stock_data.py              # 检查数据完整性
python scripts/batch_download.py --years 3      # 批量下载3年数据
python verify_price_fix.py                      # 验证价格修复（真实价格）

# === 配置相关 ===
cat stock_pool.yaml              # 查看股票池（20只）
cat config.yaml                  # 查看系统配置
cat PHASE8_SUMMARY.md            # 查看策略验证结论
```

---

## 📚 进阶阅读

### 详细文档索引

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| **QUICK_START_STREAMLIT.md** | Streamlit UI 完整说明 | 首次使用UI |
| **PHASE8_SUMMARY.md** | Phase 8 策略验证总结（2005-2024） | 理解策略边界 |
| **PROJECT_FINAL_SUMMARY.md** | 项目完整演进历史 | 了解设计决策 |
| **PRICE_FIX_COMPLETED.md** | 价格修复说明 | 理解真实价格 vs 复权价格 |
| **TODO.md** | 项目进度和已知问题 | 查看待办事项 |
| **CLAUDE.md** | 代码库说明（供AI参考） | Claude Code 协作 |

### 核心概念术语

| 术语 | 说明 |
|------|------|
| **未实现盈亏** | 当前持仓的账面浮盈浮亏（未卖出），价格波动实时变化 |
| **已实现盈亏** | 已平仓交易的实际收益（已卖出），真金白银的盈亏 |
| **换手率** | 每次调仓更换的股票比例，Phase 6E约65-72% |
| **超额收益** | 策略收益 - 基准收益（沪深300），正值=跑赢大盘 |
| **动量策略** | 基于价格趋势（MA5>MA10 + 20日涨幅）选股 |
| **月度再平衡** | 每月清仓旧持仓，重新买入最新选股结果 |
| **真实价格** | 当日真实交易价格（`adjust=""`），与券商软件一致 |
| **后复权价格** | 历史价格调整到当前基准（`adjust="hfq"`），价格虚高5-10倍 |

---

## 🆘 常见问题

### Q1: 为什么模拟盘和回测结果不一致？

**原因**：
- **模拟盘**：基于最新数据的前瞻性模拟（未来表现）
- **回测**：基于历史数据的验证（过去表现）

**对比**：
- 模拟盘收益率 = 当前持仓的浮盈浮亏
- 回测收益率 = 2022-2024历史区间的累计收益

### Q2: 如何判断策略是否适合当前市场？

查看 `PHASE8_SUMMARY.md` 第7节"策略适用边界"：
- ✅ **熊市/震荡市**：动量策略筛选强势股，超额收益显著
- ❌ **牛市**：轮动过快，容易踏空主升浪

**建议**：根据市场环境判断（看沪深300趋势）

### Q3: 价格数据是真实价格吗？

✅ **是**（2025-01-10修复后）

- 当前使用 `adjust=""` = 真实交易价格
- 与券商软件（同花顺、东方财富）完全一致
- 详见 `PRICE_FIX_COMPLETED.md`

### Q4: 回测结果可以指导实盘吗？

⚠️ **需谨慎**

**回测局限**：
- 无滑点（实盘有市价波动）
- 无冲击成本（大单影响价格）
- 无流动性约束（回测假设无限流动性）
- 佣金默认0%（实盘有佣金+印花税）

**建议**：
1. 先运行虚拟盘1个月，观察实际效果
2. 使用 `--commission 0.001` 测试佣金敏感性
3. 小资金试运行，逐步扩大规模

---

## 📞 技术支持

遇到问题请参考：
1. **QUICK_START_STREAMLIT.md** - UI使用故障排查
2. **TODO.md** - 已知问题和待办事项
3. **GitHub Issues** - 提交新问题

---

**版本**: v1.0
**更新日期**: 2025-01-10
**适用版本**: Phase 8（2005-2024历史验证）
**技术栈**: AKShare + Qlib + Streamlit + Pandas
