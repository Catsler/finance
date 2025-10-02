# Phase 0 数据验证执行清单

本文档是 Phase 0（数据源验证）的完整执行指南，预计耗时 **48 小时**。

## 📅 时间规划

| 阶段 | 时间节点 | 负责人 | 状态 |
|------|---------|--------|------|
| 环境准备 | T0 ~ T0+4h | ___ | ⬜ |
| AKShare 验证 | T0+4h ~ T0+12h | ___ | ⬜ |
| OpenBB 验证 | T0+4h ~ T0+12h | ___ | ⬜ |
| 数据对比 | T0+12h ~ T0+24h | ___ | ⬜ |
| 决策评审 | T0+24h ~ T0+48h | ___ | ⬜ |

**T0 (项目启动时间)**: __________ (待填写)

---

## ✅ 步骤 1: 环境准备（4小时）

**负责人**: ___
**截止时间**: T0 + 4h
**目标**: 配置 Python 环境并安装所有依赖

### 任务清单

- [ ] **1.1 检查 Python 版本**
  ```bash
  python --version
  # 应该输出: Python 3.8.x / 3.9.x / 3.10.x
  ```

- [ ] **1.2 创建虚拟环境（推荐）**
  ```bash
  python -m venv stock_env
  source stock_env/bin/activate  # macOS/Linux
  # stock_env\Scripts\activate   # Windows
  ```

- [ ] **1.3 安装依赖**
  ```bash
  pip install "akshare>=1.12.0"
  pip install "pandas>=1.3.0"
  pip install "qlib[all]>=0.9.0"
  ```

- [ ] **1.4 运行自检脚本**
  ```bash
  python -c "import akshare as ak; import pandas as pd; import qlib; print('✅ 环境配置成功')"
  ```

- [ ] **1.5 检查脚本可执行**
  ```bash
  python scripts/akshare-to-qlib-converter.py --help
  # 应该显示帮助信息
  ```

**验收标准**:
- Python 版本在 3.8-3.10 范围内
- 所有依赖包成功导入
- 转换脚本的 `--help` 正常显示

**常见问题**: 参考 `docs/phase0-environment-setup.md`

---

## ✅ 步骤 2: AKShare 数据验证（8小时）

**负责人**: ___
**截止时间**: T0 + 12h
**目标**: 验证 AKShare 对 A股数据的支持质量

### 任务清单

- [ ] **2.1 验证深证样本股：平安银行 (000001.SZ)**
  ```bash
  python scripts/akshare-to-qlib-converter.py \
    --symbol 000001.SZ \
    --years 3
  ```

  **检查点**:
  - [ ] 脚本运行无报错
  - [ ] 生成 CSV 文件：`~/.qlib/qlib_data/cn_data/000001.SZ.csv`
  - [ ] 日志显示 "Validation Passed"
  - [ ] 缺失率 < 5%

- [ ] **2.2 验证深证样本股：五粮液 (000858.SZ)**
  ```bash
  python scripts/akshare-to-qlib-converter.py \
    --symbol 000858.SZ \
    --years 3
  ```

  **检查点**:
  - [ ] 脚本运行无报错
  - [ ] 缺失率 < 5%
  - [ ] 收盘价全部 > 0
  - [ ] 成交量 > 0

- [ ] **2.3 验证创业板样本股：宁德时代 (300750.SZ)**
  ```bash
  python scripts/akshare-to-qlib-converter.py \
    --symbol 300750.SZ \
    --years 3
  ```

  **检查点**:
  - [ ] 脚本运行无报错
  - [ ] 缺失率 < 5%

- [ ] **2.4 验证指数：沪深300 (000300.SH)**
  ```bash
  python scripts/akshare-to-qlib-converter.py \
    --symbol 000300.SH \
    --years 3
  ```

  **检查点**:
  - [ ] 脚本运行无报错
  - [ ] 缺失率 < 5%

- [ ] **2.5 查看验证日志**
  ```bash
  cat validation_report.log
  ```

  **记录以下信息到验证报告**:
  - 每只股票的实际记录数
  - 缺失率百分比
  - 遇到的异常（网络超时、数据格式错误等）

**验收标准**:
- 4 个标的全部验证通过（缺失率 < 5%）
- 无致命错误（Fatal Error）
- 数据文件成功生成

**失败处理**:
- 如果缺失率 5%-10%：记录到报告，继续验证其他数据源
- 如果缺失率 > 10%：立即启动 Plan B（见步骤 5）

---

## ✅ 步骤 3: OpenBB 数据验证（8小时，可选）

**负责人**: ___
**截止时间**: T0 + 12h
**目标**: 验证 OpenBB 是否支持 A股市场

> ⚠️ **注意**: 此步骤可与步骤 2 并行进行

### 任务清单

- [ ] **3.1 安装 OpenBB**
  ```bash
  pip install openbb
  ```

- [ ] **3.2 测试 A股数据获取**

  创建测试脚本 `test_openbb.py`:
  ```python
  from openbb_terminal.sdk import openbb as obb

  # 测试深证股票
  try:
      df = obb.equity.price.historical("000001.SZ")
      print(f"✅ OpenBB 支持 A股: {len(df)} 条记录")
      print(df.head())
  except Exception as e:
      print(f"❌ OpenBB 不支持 A股: {e}")
  ```

  运行:
  ```bash
  python test_openbb.py
  ```

- [ ] **3.3 记录结果**

  **如果成功**:
  - [ ] 记录返回的字段列表（open, close, high, low, volume 等）
  - [ ] 对比 AKShare 的数据（收盘价是否一致）
  - [ ] 记录数据完整性（缺失率）

  **如果失败**:
  - [ ] 记录错误信息（不支持 A股 / API 限制 / 其他）
  - [ ] 在验证报告中标记 "OpenBB 不可用"

**验收标准**:
- 明确记录 OpenBB 对 A股的支持情况
- 如果支持，提供数据质量对比

**预期结果**:
- OpenBB 可能不直接支持 A股（需验证）
- 如不支持，AKShare 作为唯一数据源

---

## ✅ 步骤 4: 数据一致性对比（12小时）

**负责人**: ___
**截止时间**: T0 + 24h
**目标**: 对比不同数据源的一致性（如果有多个可用）

### 任务清单

- [ ] **4.1 读取 AKShare 数据**
  ```python
  import pandas as pd

  akshare_data = pd.read_csv("~/.qlib/qlib_data/cn_data/000001.SZ.csv")
  print(akshare_data.head())
  ```

- [ ] **4.2 对比收盘价**（如果 OpenBB 可用）
  ```python
  # 伪代码
  merge_df = pd.merge(akshare_data, openbb_data, on='date', suffixes=('_ak', '_obb'))
  merge_df['diff'] = (merge_df['close_ak'] - merge_df['close_obb']) / merge_df['close_ak']

  max_diff = merge_df['diff'].abs().max()
  print(f"最大偏差: {max_diff:.2%}")
  ```

- [ ] **4.3 判断一致性**

  **标准**:
  - 偏差 < 2%: 一致性良好 ✅
  - 偏差 2%-5%: 可接受 ⚠️
  - 偏差 > 5%: 数据质量存疑 ❌

- [ ] **4.4 分析差异原因**（如有差异）
  - [ ] 复权方式不同（前复权 vs 后复权）
  - [ ] 数据源不同（东方财富 vs 雅虎财经）
  - [ ] 时间对齐问题（时区、交易日历）

**验收标准**:
- 完成至少 1 只股票的数据对比
- 记录对比结果和差异原因

---

## ✅ 步骤 5: 决策评审（24小时）

**负责人**: ___
**截止时间**: T0 + 48h
**目标**: 根据验证结果做出 Go/No-Go 决策

### 任务清单

- [ ] **5.1 汇总验证结果**

  填写 `docs/phase0-validation-report-template.md`，包括：
  - [ ] 基本信息（日期、负责人、环境）
  - [ ] 验证结果表格（每个数据源的可用性）
  - [ ] 数据质量指标（缺失率、一致性）
  - [ ] 遇到的问题清单

- [ ] **5.2 评估数据源**

  | 数据源 | 可用性 | 数据质量 | 稳定性 | 推荐度 |
  |--------|--------|---------|--------|--------|
  | AKShare | ✅/❌ | 缺失率 X% | 爬虫依赖 | ⭐⭐⭐⭐ |
  | OpenBB | ✅/❌ | 缺失率 X% | API 限制 | ⭐⭐⭐ |

- [ ] **5.3 做出决策**

  **Go 条件**（进入 Phase 1）:
  - [x] 至少 1 个数据源可用
  - [x] 数据缺失率 < 5%
  - [x] 转换脚本运行稳定

  **No-Go 条件**（启动 Plan B）:
  - [ ] 所有数据源不可用
  - [ ] 数据缺失率 > 10%
  - [ ] 技术风险过高

- [ ] **5.4 选择主力数据源**

  **决策规则**:
  - 如果 AKShare 可用且质量合格 → 选择 AKShare
  - 如果 AKShare 不稳定 → 选择 OpenBB 或混合使用
  - 如果都不理想 → 启动 Plan B

- [ ] **5.5 更新 TODO.md**

  - [ ] 标记 Phase 0 状态为 "✅ 已完成"
  - [ ] 填写实际完成时间
  - [ ] 添加 Phase 1 的启动计划

**验收标准**:
- 验证报告完整填写
- Go/No-Go 决策明确
- 团队达成共识

---

## 🚨 Plan B: 备选方案

如果主数据源验证失败，按以下优先级启动备选方案：

### Plan B1: 降低数据要求
**触发条件**: 缺失率在 5%-10% 之间

**行动**:
```bash
# 缩短时间窗口（3年 → 1年）
python scripts/akshare-to-qlib-converter.py \
  --symbol 000001.SZ \
  --years 1

# 或只验证沪市（减少样本）
python scripts/akshare-to-qlib-converter.py \
  --symbol 600000.SH \
  --years 3
```

---

### Plan B2: 切换到 Yahoo Finance
**触发条件**: AKShare 和 OpenBB 都不可用

**行动**:
```bash
pip install yfinance

# 测试脚本
python -c "import yfinance as yf; df = yf.download('000001.SZ', period='3y'); print(df.head())"
```

**注意**: Yahoo Finance 的复权数据可能有问题，需谨慎验证。

---

### Plan B3: 申请 Tushare 试用配额
**触发条件**: 免费数据源全部失败

**行动**:
1. 注册 Tushare 账号：https://tushare.pro/register
2. 发邮件说明学术/研究用途
3. 申请临时高额度（通常可获得 500-1000 积分/天）

---

### Plan B4: 使用公开数据集
**触发条件**: 所有 API 数据源失败

**行动**:
1. 搜索 Kaggle/GitHub 的 A股历史数据包
2. 下载 CSV 文件（需确认数据来源和质量）
3. 转换为 Qlib 格式

**示例**:
- [Kaggle: China Stock Market Data](https://www.kaggle.com/datasets)
- GitHub: 搜索 "A股历史数据"

---

## 📊 验收标准总览

### 数据质量
- [x] 缺失率 < 5%（理想）或 < 10%（可接受）
- [x] 所有收盘价 > 0
- [x] 累计成交量 > 0
- [x] 至少 3 只股票验证通过

### 工具可用性
- [x] 转换脚本可独立运行
- [x] 生成标准格式的 CSV 文件
- [x] 验证日志清晰可读

### 文档完整性
- [x] 环境配置文档完成
- [x] 执行清单全部勾选
- [x] 验证报告已填写

---

## 📝 记录模板

在执行过程中，请记录以下信息（用于填写验证报告）：

```markdown
### 执行记录

**日期**: 2025-XX-XX
**执行人**: ___
**耗时**: ___ 小时

#### 成功项
- 股票 XXX 验证通过，缺失率 X.X%
- 股票 YYY 验证通过，缺失率 X.X%

#### 问题项
- 股票 ZZZ 出现网络超时，重试 3 次后成功
- OpenBB 不支持 A股，已放弃

#### 决策
- 选择 AKShare 作为主力数据源
- 下一步: 进入 Phase 1 - Qlib 回测
```

---

## 📞 支持资源

遇到问题时：
1. 查看 `docs/phase0-environment-setup.md` 的常见问题
2. 查看 `config.yaml` 的标准配置
3. 查看 `validation_report.log` 的详细日志
4. 联系项目负责人

---

**最后更新**: 2025-10-01
**维护者**: Agent 2 (流程设计师)
