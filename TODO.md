# TODO - Phase 6F 止盈策略研究

**最后更新**：2025-10-11 18:30

## 当前进度

| 行动项 | 目标产出 | 状态 |
|-------|---------|------|
| 🔴 市场环境识别模块 | `utils/market_regime.py` + `docs/market_regime_logic.md` | ✅ |
| 🟢 收益分布分析 | `results/phase6d_profit_distribution.csv` | ✅ |
| 🟢 固定止盈实现 | `scripts/phase6d_backtest.py` (新增 `--take-profit` 参数) | ✅ |
| 🟢 止盈策略回测 | `results/phase6f_takeprofit_comparison.md` | ✅ |

**图例**：✅ 完成 | ⏳ 进行中 | 🔜 待开始 | ⚠️ 受阻

---

## 执行清单

### 🔴 首要：市场环境识别（1小时）

**目标**：让策略能自动切换"动态止损 vs 无止损"

**核心指标**（3选2即可）：
- 波动率：std(20日收益率) > 阈值 → 震荡
- 趋势强度：MA5/MA10 斜率 < 阈值 → 震荡
- 最大回撤：滚动20日最大回撤 > 阈值 → 震荡

**执行**：
```bash
# 实现震荡/单边市场环境识别
# 创建 utils/market_regime.py 和 docs/market_regime_logic.md

# 验证
pytest tests/test_market_regime.py  # 如果有测试
```

---

### 🟡 收尾：2024年验证（30分钟）

**唯一任务**：补充2024年失效分析 + 参数敏感性表

**执行**：
```bash
python scripts/phase6f_final_review.py
# 产出：2024逐月分析 + 参数敏感性表
```

**预期产出**：
- `results/phase6f_2024_monthly_review.csv` - 逐月持仓/止损触发
- `results/phase6f_param_sensitivity.md` - ATR倍数/回撤阈值对比表

---

## 暂缓项（Phase 7）

- 移动止损
- OCO订单
- 自适应仓位调整

---

<details>
<summary>📖 可选深入：设计思路与风险分析</summary>

### 为什么先做市场环境识别？

**Phase 6E 核心发现**：
- 动态止损在震荡市 +19.90%，牛市 -36.25%
- 需要自动判断何时启用止损/止盈策略

**识别方案**：
- **波动率指标**：std(20日收益率) > 2% → 震荡市
- **趋势强度指标**：MA5/MA10 斜率 < 0.001 → 震荡市
- **回撤指标**：滚动20日最大回撤 > 8% → 震荡市

**决策规则**：
```python
if 震荡市环境:
    启用动态止损
else:
    无止损（顺势持有）
```

---

### 2024年失效的根本原因？

**Phase 6F 发现**：
- 动态止损过早清仓，错过牛市主升浪
- 20日 ATR 在快速上涨时误判为风险信号
- 需要区分"健康回调"vs"趋势反转"

**复盘重点**：
1. 逐月分析2024年止损触发情况
2. 对比不同ATR倍数（1.0/1.5/2.0）的影响
3. 评估跟踪回撤阈值（5%/8%/10%）的效果

---

### 固定止盈的参数选择逻辑？

**设计思路**：
1. 先跑历史收益分布（25%/50%/75%分位数）
2. 根据分位数确定梯度
3. 避免"过早止盈错失大牛股"

**实际测试结果**（2022-2024，105个持仓周期）：
```
中位数(p50): -0.10%
75%分位(p75): 6.74%
推荐阶梯: 10%, 15%
```

**风险提示**：
- 固定止盈在超级牛市中会降低收益
- 建议保留"无止盈"作为对照组

---

### Phase 6F 核心结论（已完成部分）

**方案A：季度调仓** ❌
- 结果：2023年-13.62%（vs月度-0.03%，恶化13.59个百分点）
- 结论：频率降低损失收益，不可行

**方案B：持仓稳定性过滤** ❌
- 结果：与baseline完全相同（无效果）
- 根因：2023年市场波动剧烈，旧仓位持续失效
- 结论：震荡市环境下无法发挥作用

**方案C：固定止盈（10%, 15%）** ❌
- 结果：2023年-26.79%（vs baseline +1.03%，恶化27.82个百分点）
- 结果：2024年+17.84%（vs baseline +51.54%，恶化33.70个百分点）
- 根因：中位数为负，p75仅6.74%，止盈梯度与收益分布严重不匹配
- 根因：动量策略依赖少数强势股的尾部收益，固定止盈系统性切断尾部收益
- 结论：固定止盈从根本上不适用于动量策略
- 详见：[phase6f_takeprofit_comparison.md](results/phase6f_takeprofit_comparison.md)

**核心认知**：
- 动量策略依赖频繁调仓捕捉机会
- 动量策略依赖少数强势股的尾部收益
- 高换手是策略特性，难以简单优化
- **Phase 6E配置（20股+月调+无止盈）已是最佳可达方案**

---

### 风险提示 ⚠️

**成本敏感性**：
- 佣金≥0.1%时2023年收益趋零（-0.03%）
- 实盘需极低成本券商（综合<0.1%）

**市场环境依赖**：
- 适合趋势市，震荡市需谨慎
- 建议根据市场环境动态调整仓位

**止盈策略风险** ❌：
- 固定止盈已验证失败（2023/2024年均显著恶化收益）
- 不建议使用固定止盈策略
- Phase 6E无止盈配置为最佳方案

</details>

---

## 📊 项目整体进度

| Phase | 目标 | 状态 | 完成时间 | 关键成果 |
|-------|------|------|---------|---------|
| Phase 0 | 数据源验证 | ✅ 完成 | 2025-10-01 | AKShare验证通过 |
| Phase 1 | 环境搭建 | ✅ 完成 | 2025-10-01 | 10只股票池，3年数据 |
| Phase 2 | 策略回测 | ✅ 完成 | 2025-10-01 | MA20/MA60策略，年化11.39% |
| Phase 3 | 策略优化 | ✅ 完成 | 2025-10-01 | MA5/MA10最优，Sharpe 0.96 |
| Phase 4 | 风控优化 | ✅ 完成 | 2025-10-01 | 双重止损策略，Sharpe 1.02 |
| Phase 5 | 前端可视化 | ✅ 完成 | 2025-10-01 | Jupyter Notebook仪表盘 |
| Phase 6A | 动态选股验证 | ✅ 完成 | 2025-10-01 | 动态选股+18.16%超额收益 |
| Phase 6B | 参数灵敏度测试 | ✅ 完成 | 2025-10-01 | 最优参数确认：0%+MA5>MA10 |
| Phase 6C | 真实换手额记录 | ✅ 完成 | 2025-10-01 | 实际成本1.17%，净超额16.98% |
| Phase 6D | 三年稳健性验证 | ✅ 完成 | 2025-10-02 | 2023年失效已定位，Sharpe已修正 |
| Phase 6E | 股票池扩展 | ✅ 完成 | 2025-10-02 | 20只股票池修复2023年问题 |
| Phase 6F | 降低换手率优化 | ✅ 完成 | 2025-10-11 | 固定止盈验证失败，Phase 6E为最优方案 |
| Phase 7 | 2025年实盘跟踪 | ✅ 完成 | 2025-10-02 | 首次跑输沪深300，揭示牛市局限性 |
| Phase 8 | 长周期回测 | ✅ 完成 | 2025-10-02 | 牛市失效-36.25%，策略定位修正 |

**总体完成度**: 100% (14/14 Phases) 🎉

---

## 🚀 快速命令参考

### 数据下载
```bash
# 单只股票
python scripts/akshare-to-qlib-converter.py --symbol 000001.SZ --years 3

# 批量下载（20只股票池）
python scripts/batch_download.py --years 3
```

### 策略回测

**Phase 6E: 推荐配置**（20只股票池）
```bash
# 三年完整回测（2022-2024）
python scripts/phase6d_backtest.py --full

# 单年回测
python scripts/phase6d_backtest.py --year 2023

# 参数化测试
python scripts/phase6d_backtest.py --full --momentum-threshold -5.0
python scripts/phase6d_backtest.py --full --rebalance-freq quarterly

# 10只池（legacy）
python scripts/phase6d_backtest.py --full --pool small_cap
```

**Phase 2-5: 固定持仓策略**（10只股票池）
```bash
python scripts/momentum_backtest.py        # Phase 2: 基础动量策略
python scripts/strategy_optimization.py    # Phase 3: 参数优化
python scripts/risk_control_backtest.py    # Phase 4: 风控优化
```

### Jupyter Notebook
```bash
jupyter notebook
# 打开 notebooks/stock_dashboard.ipynb
```

---

## 📞 相关文档

**核心文档** ⭐：
- [PROJECT_FINAL_SUMMARY.md](PROJECT_FINAL_SUMMARY.md) - 项目最终总结（必读）
- [README.md](README.md) - 项目说明
- [TODO.md](TODO.md) - 本文档

**Phase总结**：
- [PHASE6E_SUMMARY.md](PHASE6E_SUMMARY.md) - 20股池验证（当前推荐配置）
- [PHASE6F_SUMMARY.md](PHASE6F_SUMMARY.md) - 降低换手率尝试（未达标）
- [PHASE7_2025_TRACKING.md](PHASE7_2025_TRACKING.md) - 2025年跟踪（发现牛市局限性）
- [PHASE8_SUMMARY.md](PHASE8_SUMMARY.md) - 长周期回测（策略适用边界）

**配置文件**：
- [stock_pool.yaml](stock_pool.yaml) - 20只股票池配置
- [config.yaml](config.yaml) - 系统配置

---

**最后更新**: 2025-10-11
**更新者**: Claude (AI Agent)
**当前阶段**: Phase 6F（止盈策略探索）

**策略定位**: 熊市/震荡市防御型策略（vs300超额+19.90%），牛市失效需切换Buy & Hold
