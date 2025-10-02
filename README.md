# Stock 量化交易系统

基于免费数据源的 A股量化交易系统，采用 Qlib 框架进行策略回测与优化。

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
- [PHASE6E_SUMMARY.md](PHASE6E_SUMMARY.md) - 20只股票池验证（当前推荐配置）
- [PHASE6F_SUMMARY.md](PHASE6F_SUMMARY.md) - 降低换手率优化尝试（未达标）

---

## 🎯 项目目标

构建一个轻量级的量化交易系统，支持：
- A股市场数据获取与处理
- 多因子策略回测
- 策略优化与可视化

## 📊 当前进展

**Phase 0: 数据源验证**（48小时） - 🟡 进行中
- 验证 AKShare/OpenBB 对 A股的支持情况
- 开发数据转换脚本
- 完成基础文档和工具准备

详细进度见 [TODO.md](TODO.md)

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

- [TODO.md](TODO.md) - 任务追踪与进度管理
- [config.yaml](config.yaml) - 统一配置文件
- [docs/](docs/) - 详细文档目录（Phase 0 完成后填充）

## ⚠️ 当前限制

- **数据源**: 仅支持免费数据源，可能存在爬虫依赖风险
- **数据频率**: 当前仅支持日线数据（分钟/Tick 级别需付费 API）
- **市场覆盖**: 当前仅验证沪深市场，其他市场待扩展

## 🎓 参考资源

- [Qlib 官方文档](https://qlib.readthedocs.io/)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [OpenBB 文档](https://docs.openbb.co/)

## 📝 更新日志

- **2025-10-01**: Phase 0 启动，创建项目结构和任务分配

---

**License**: MIT
**Maintainer**: ___（待填写）
