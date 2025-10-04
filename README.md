# Stock 量化交易系统

基于免费数据源的 A股量化交易系统，采用 Qlib 框架进行策略回测与优化。

> ⚠️ **重要风险提示**（Phase 8发现，2025-10-02）
>
> **仅适用熊市/震荡市**，牛市失效严重：
> - ✅ 熊市/震荡（2022-2024）：vs300超额 **+19.90%**
> - ❌ 牛市全程（2007/2019）：vs300超额 **-36.25%**
>
> **使用建议**：熊市/震荡使用本策略，牛市切换Buy & Hold
>
> 详见 → [PHASE8_SUMMARY.md](PHASE8_SUMMARY.md)

---

## 🚀 快速开始

### 前提条件
- Python 3.8+
- 已完成Phase 1数据下载（运行`python scripts/batch_download.py --years 3`）

### ⚠️ 交易成本警告

**当前推荐配置（Phase 6E）在高成本下收益显著下降**：
- 无佣金：2023年+6.10%
- **0.1%佣金**：2023年**-0.03%**（接近盈亏平衡）
- 0.2%佣金：2023年-5.91%

**实盘建议**：
- 需要极低成本券商（综合<0.1%）
- 适合趋势年份，震荡年份需谨慎
- 详见：[PHASE6E_SUMMARY.md - 交易成本敏感性](PHASE6E_SUMMARY.md#⚠️-风险提醒)

### 推荐配置（Phase 6E验证）

**三年回测（2022-2024，20只股票池）**：
```bash
python scripts/phase6d_backtest.py --full
```

**关键指标**：
- 2023年收益：**+6.10%** ✅ (vs 10只池-18.16%)
- vs沪深300超额：三年全部跑赢（+23.75%, +17.85%, +21.52%）
- 月均换手率：60-75%

**其他命令**：
```bash
# 单年回测
python scripts/phase6d_backtest.py --year 2023

# 参数化测试
python scripts/phase6d_backtest.py --full --momentum-threshold -5.0

# 季度调仓
python scripts/phase6d_backtest.py --full --rebalance-freq quarterly

# 10只池（legacy）
python scripts/phase6d_backtest.py --full --pool small_cap
```

**其他策略（Phase 2-5: 固定持仓）**：
```bash
# 使用10只股票池
python scripts/momentum_backtest.py           # Phase 2: 基础动量策略
python scripts/strategy_optimization.py       # Phase 3: 参数优化
python scripts/risk_control_backtest.py       # Phase 4: 风控优化
```

**详细文档**:
- [PROJECT_FINAL_SUMMARY.md](PROJECT_FINAL_SUMMARY.md) - **项目最终总结**（必读⭐）
- [PHASE6E_SUMMARY.md](PHASE6E_SUMMARY.md) - 20只股票池验证（当前推荐配置）
- [PHASE6F_SUMMARY.md](PHASE6F_SUMMARY.md) - 降低换手率优化尝试（未达标）
- [PHASE7_2025_TRACKING.md](PHASE7_2025_TRACKING.md) - 2025年跟踪（发现牛市局限性）

---

## 💼 实盘部署指南

### ⚠️ 适用性评估

**推荐使用** ✅：
- 机构投资者（拥有极低成本<0.05%）
- 量化私募（作为多策略组合）
- 在**熊市/震荡市**使用（超额+12% ~ +24%）

**不推荐使用** ❌：
- 个人投资者（成本通常>0.1%，策略失效）
- 在**牛市**长期持有（2025年vs300 -4.58%）
- 高成本券商（佣金>0.1%时2023年转亏损）

### 📋 部署检查清单

**1. 成本控制（硬性要求）**
```
[ ] 佣金率 <0.05%（单边，含规费）
[ ] 滑点控制 <0.02%（需算法交易）
[ ] 综合成本 <0.1%（往返）
```
⚠️ **不满足上述条件请勿使用**

**2. 市场环境判断**
```yaml
熊市/震荡市（沪深300近3月涨幅<5%）:
  策略仓位: 80-100%
  指数仓位: 0-20%

牛市（沪深300近3月涨幅>10%）:
  策略仓位: 30-50%  # 降低
  指数仓位: 50-70%  # 增加
```

**3. 月度执行流程**
```bash
# 每月最后一个交易日14:00-14:30执行选股
python scripts/phase6d_backtest.py --year 2025

# 检查市场环境，决定仓位（熊市100% vs 牛市50%）
# 14:45-15:00提交限价单（分批委托，避免冲击成本）
```

**详细说明**: 参见 [PROJECT_FINAL_SUMMARY.md - 实盘建议](PROJECT_FINAL_SUMMARY.md#💡-实盘建议)

---

## 🎯 项目目标

构建一个轻量级的量化交易系统，支持：
- A股市场数据获取与处理
- 多因子策略回测
- 策略优化与可视化

## 📊 项目状态

**✅ 已完成** - Phase 0-7 全部完成（2025-10-02）

- ✅ Phase 0-5：数据验证 → 策略开发 → 可视化
- ✅ Phase 6A-6E：动态选股 → 参数优化 → 20股池验证
- ✅ Phase 6F：降低换手率尝试（未达标，Phase 6E为最佳）
- ✅ Phase 7：2025年实盘跟踪（发现牛市局限性）

详细进度见 [TODO.md](TODO.md) | **完整总结**: [PROJECT_FINAL_SUMMARY.md](PROJECT_FINAL_SUMMARY.md)

## 🏗️ 项目结构

```
Stock/
├── config.yaml                 # 统一配置文件
├── TODO.md                     # 任务追踪
├── README.md                   # 项目说明
├── docs/                       # 文档目录
│   ├── phase0-environment-setup.md              # 环境配置指南
│   ├── phase0-data-validation-checklist.md      # 数据验证清单
│   ├── phase0-validation-report-template.md     # 验证报告模板
│   └── phase0-validation-report-FILLED.md       # 已填写的验证报告
├── scripts/                    # 脚本目录
│   └── akshare-to-qlib-converter.py             # 数据转换脚本
├── data/                       # 数据目录（待创建）
├── strategies/                 # 策略目录（待创建）
└── notebooks/                  # Jupyter 笔记本（待创建）
```

## 🚀 快速开始

### 1. 环境准备
```bash
# Python 3.8-3.10
pip install "akshare>=1.12.0"
pip install "pandas>=1.3.0"
pip install "qlib[all]>=0.9.0"
```

### 2. 数据验证（Phase 0）
```bash
# 验证单只股票数据
python scripts/akshare-to-qlib-converter.py --symbol 000001.SZ --years 3

# 查看验证日志
cat validation_report.log
```

详细步骤见 `docs/phase0-data-validation-checklist.md`

## 📋 任务分配

Phase 0 采用并行开发模式，4个独立任务可同时进行：

| 任务 | 负责人 | 输出文件 | 状态 |
|------|--------|---------|------|
| Task-A | Agent 1 | `docs/phase0-environment-setup.md` | ⬜ |
| Task-B | Agent 2 | `docs/phase0-data-validation-checklist.md` | ⬜ |
| Task-C | Agent 3 | `docs/phase0-validation-report-template.md` | ⬜ |
| Task-D | Agent 4 | `scripts/akshare-to-qlib-converter.py` | ⬜ |

详见 [TODO.md - 任务追踪](TODO.md)

## 🔧 技术栈

### 数据源
- **AKShare** (优先) - 免费无限制，支持 A股全市场
- **OpenBB** (备选) - 需验证 A股支持情况
- **Yahoo Finance** (备选) - 复权数据待确认

### 核心框架
- **Qlib** - 微软开源的量化投资平台
- **Pandas** - 数据处理
- **NumPy** - 数值计算

### 开发工具
- Python 3.8-3.10
- Jupyter Notebook（可选，用于策略实验）

## 📖 文档索引

**核心文档** ⭐：
- [PROJECT_FINAL_SUMMARY.md](PROJECT_FINAL_SUMMARY.md) - 项目最终总结（策略评价、实盘建议、风险分析）
- [README.md](README.md) - 项目说明（本文档）
- [TODO.md](TODO.md) - 任务追踪（完整历史）

**Phase总结**：
- [PHASE6E_SUMMARY.md](PHASE6E_SUMMARY.md) - 20股池验证（当前推荐配置）
- [PHASE6F_SUMMARY.md](PHASE6F_SUMMARY.md) - 降低换手率尝试（未达标）
- [PHASE7_2025_TRACKING.md](PHASE7_2025_TRACKING.md) - 2025年跟踪（发现牛市局限性）
- [PHASE0-5_SUMMARY.md](PHASE0_SUMMARY.md) - 早期Phase总结

**配置文件**：
- [stock_pool.yaml](stock_pool.yaml) - 20只股票池配置
- [config.yaml](config.yaml) - 系统配置

## ⚠️ 策略局限性

**成本敏感性** ⚠️⚠️⚠️：
- 0.1%佣金让2023年收益从+6.10% → -0.03%
- **实盘需极低成本（<0.1%），否则策略失效**
- 个人投资者成本通常>0.1%，**不推荐使用**

**市场环境依赖** ⚠️⚠️：
- ✅ 熊市/震荡市：vs300超额+12% ~ +24%
- ❌ 牛市：vs300超额-4.58%（2025年首次跑输）
- **需根据市场环境动态调整仓位**

**详细分析**: [PROJECT_FINAL_SUMMARY.md - 核心风险](PROJECT_FINAL_SUMMARY.md#⚠️-核心风险与局限性)

## 🎓 参考资源

- [Qlib 官方文档](https://qlib.readthedocs.io/)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [OpenBB 文档](https://docs.openbb.co/)

## 📝 更新日志

- **2025-10-02**: Phase 7完成，2025年跟踪揭示牛市局限性，项目归档
- **2025-10-02**: Phase 6F完成，降低换手率尝试未达标
- **2025-10-02**: Phase 6E完成，20股池修复2023年问题
- **2025-10-01**: Phase 0-6D完成，基础策略开发+三年稳健性验证

---

## 📌 版本信息

- **版本**: v1.0-final
- **完成日期**: 2025-10-02
- **策略状态**: ✅ 可用（机构级，需极低成本）
- **实盘建议**: 熊市/震荡市80-100%仓位，牛市30-50%仓位

---

**License**: MIT
**Maintainer**: Elie (assisted by Claude Code)

*本项目仅供学习研究使用，不构成投资建议。*
