# TODO - 项目任务追踪

**最后更新**：2025-12-18 16:13

---

## 🚧 Phase 1: 数据源扩展准备 (2025-10-16启动)

**目标**：为接入AData、Tushare等多数据源做架构准备

| 阶段 | 任务 | 状态 | 产出 | 负责 |
|------|------|------|------|------|
| 1.1 | adjfactor验证与回测对比 | ✅ | `results/adjfactor_analysis_findings.md` | 完成 |
| 1.2 | 配置整合 (Pydantic) | ✅ | `config/settings.py` + `results/phase1_verification.md` | Agent A-E 完成 |
| 2.1 | DataProvider抽象层 | ✅ | `utils/data_provider/base.py` + `exceptions.py` | Agent G-H 完成 |
| 2.2 | AKShare Provider实现 | ✅ | `utils/data_provider/akshare_provider.py` | Agent I 完成 |
| 2.3 | AData Provider占位 | ✅ | `utils/data_provider/adata_provider.py` | Agent K 完成 |
| 2.4 | Converter脚本重构 | ✅ | `scripts/akshare-to-qlib-converter.py` (Phase 2) | Agent J 完成 |
| 3.1 | 100只股票池设计 | ✅ | `results/stock_pool_100_design.csv` | Agent L 完成 |
| 3.2 | 配置系统扩展 | ✅ | `stock_pool.yaml` (large_cap 100只) | Agent M 完成 |
| 3.3 | 批量下载优化 | ✅ | `scripts/batch_download.py` (并行+续传) | Agent N 完成 |
| 3.4 | 批量下载执行 | ✅ | 96/100只成功下载 (96%成功率) | Agent 完成 |
| 3.5 | 回测脚本适配 | ✅ | `scripts/phase6d_backtest.py` (96股池测试通过) | 完成 |
| 3.6 | 回测性能评估 | ✅ | `results/phase3_96stocks_comparison.md` | 完成 |

**当前焦点**: Phase 3 完成 ✅ (核心结论：20只精选池优于96只扩展池，保持Phase 6E配置)

---

## 🚧 Phase 6G: 全市场 Universe 同步 (2025-12-15)

**目标**：同步全量 A 股股票列表（可选下载历史行情），为全市场筛选/回测做数据底座。

| 任务 | 状态 | 产出 |
|------|------|------|
| 同步股票列表（SH/SZ，可选BJ） | ✅ | `scripts/phase6g_sync_all_a_shares.py` + `results/phase6g_a_share_universe.csv` |
| 可选下载历史行情（建议限量试跑） | ⏳ | `results/phase6g_a_share_price_sync_report.json` |

---

## 🖥️ Dashboard v0.2: 60分K + KDJ 图表（2025-12-18）

**目标**：支持“信号触发后人工确认/干预”的图表视图（60分K + KDJ + 成交标记 + 成本线）。

**详细计划**：[docs/implementation_plan_v0.2.md](docs/implementation_plan_v0.2.md)

| 模块 | 优先级 | 状态 |
|------|--------|------|
| 数据契约（candles API） | P0 | 🔜 待启动 |
| 60m 图表渲染（K线+VOL+KDJ） | P0 | 🔜 待启动 |
| 成交标记与悬浮（fills） | P0 | 🔜 待启动 |
| 成本线（positions.avg_cost） | P0 | 🔜 待启动 |
| 轮询策略调整 | P0 | 🔜 待启动 |
| 日线趋势过滤（daily_trend） | P1 | 🔜 待启动 |
| 分时图 | P1 | 🔜 待启动 |

### ✅ Phase 2 完成总结

**完成时间**: 2025-10-16
**开发方式**: 并行Agent开发（Agent G-K）

**产出文件**:
- `utils/data_provider/__init__.py` (~70行) - 包初始化和导出
- `utils/data_provider/base.py` (~300行) - 抽象基类
- `utils/data_provider/exceptions.py` (~150行) - 异常体系
- `utils/data_provider/akshare_provider.py` (~350行) - AKShare实现
- `utils/data_provider/adata_provider.py` (~120行) - AData占位
- `scripts/akshare-to-qlib-converter.py` (重构) - 使用新Provider

**核心特性**:
1. ✅ 统一的数据接口（BaseDataProvider）
2. ✅ 完整的异常体系（6个异常类）
3. ✅ AKShare完整实现（支持股票+指数数据）
4. ✅ AData占位实现（预留接口）
5. ✅ CLI工具重构（向后兼容）
6. ✅ 类型安全（完整类型注解）

**验证状态**: ✅ 所有模块导入正常，CLI接口工作正常

### ✅ 阶段1.2 验收结果

**验收状态**: ✅ **PASSED** - 零回归，配置整合成功

| 验收项 | 要求 | 实际结果 | 状态 |
|--------|------|---------|------|
| **配置加载** | 正常读取 stock_pool.yaml | 20只股票正确加载 | ✅ 通过 |
| **回测执行** | 无报错，正常运行 | 三年回测全部成功 | ✅ 通过 |
| **结果一致性** | 与 Phase 6E 基线一致 | 100%一致（0.00%差异） | ✅ 通过 |
| **类型验证** | Pydantic 验证生效 | 股票代码格式自动验证 | ✅ 通过 |
| **向后兼容** | 保持旧接口可用 | load_stock_pool() 兼容 | ✅ 通过 |

**回测收益验证** (2022-2024):
```
2022: +3.33% (vs 沪深300 -21.27%, 超额+24.60%) ✅
2023: +1.03% (vs 沪深300 -11.75%, 超额+12.78%) ✅
2024: +51.54% (vs 沪深300 +18.65%, 超额+32.89%) ✅
```

**详细报告**: [Phase 1 验证报告](results/phase1_verification.md)

### 🔧 阶段1.2 并行开发计划 (已完成 ✅)

**Agent A** (基础架构 1-2h): `config/settings.py` Pydantic BaseSettings ✅
**Agent B** (配置迁移 1h): YAML → Pydantic ✅
**Agent C** (脚本更新 1-2h): `phase6d_backtest.py`, `batch_download.py` ✅
**Agent D** (验证测试 30min): 运行测试确认配置系统正常 ✅
**Agent E** (回测验证 1h): 验证策略收益与 Phase 6E 基线一致 ✅

---

## 🔬 Phase 9: 数据复权验证与基础设施优化 (2025-10-17启动)

**目标**：渐进式验证数据链路，基于实测决策是否扩展全市场

**总耗时**：5-8天（1-1.5周）
**开发方式**：并行Agent开发（3轮并行）
**核心原则**：小步快跑、数据驱动、最小可行增量

---

### Phase 9.1: 复权验证与最小抽象（2-3天）

| Agent | 任务 | 耗时 | 产出 | 独立性 | 状态 |
|-------|------|------|------|--------|------|
| **Agent A** | 复权数据验证 | 1天 | `results/adjfactor_verification.txt` | ✅ 独立 | ✅ 已完成 |
| **Agent B** | 配置加载器 | 0.5天 | `config/__init__.py` | ✅ 独立 | ✅ 已完成 |
| **Agent C** | Smoke Test框架 | 0.5天 | `tests/test_smoke.py` | ✅ 独立 | ✅ 已完成 |
| **Agent D** | DataProvider接口 | 1天 | `utils/data_provider.py` | ❌ 依赖A+B | ✅ 已完成 |

**并行策略**：
- 第1轮：Agent A + B + C 同时启动（3个并行）
- 第2轮：Agent D 等待A+B完成后启动

**Agent A任务详情**：
```python
# scripts/verify_adjfactor.py
# 对比3只高分红股票：
# - 贵州茅台 (600519.SH)
# - 工商银行 (601398.SH)
# - 中国神华 (601088.SH)
# 验证：AKShare adjust='qfq' vs adjust='' vs 东方财富
# 决策：误差<1% → 直接用AKShare；否则自建adjfactor
```

**Agent B任务详情**：
```python
# config/__init__.py
from dataclasses import dataclass
import yaml

@dataclass
class Config:
    data_dir: str
    pools: dict  # small_cap/medium_cap/large_cap
    backtest: dict

def load_config() -> Config:
    # 加载 config.yaml + stock_pool.yaml
    # 返回统一Config对象
```

**Agent C任务详情**：
```python
# tests/test_smoke.py
def test_backtest_end_to_end():
    # 1只股票 × 1个月回测
    # 不抛异常即通过
```

**验收标准**：
- [ ] AKShare qfq误差<1% OR 自建adjfactor完成 （待人工验证）
- [x] 配置统一加载正常 ✅
- [x] Smoke测试通过 ✅ (11/11 tests passed - 含复权数据验证)
- [x] DataProvider接口清晰 ✅

---

### Phase 9.2: 实测与性能数据（2-3天）

| Agent | 任务 | 耗时 | 产出 | 独立性 | 状态 |
|-------|------|------|------|--------|------|
| **Agent E** | 20只股票复权回测 | 1天 | `results/phase9_20stocks_qfq_comparison.md` | ✅ 独立 | 🔜 待启动 |
| **Agent F** | Combo-A失败复盘 | 1天 | `results/combo_a_failure_analysis.md` | ✅ 独立 | 🔜 待启动 |
| **Agent G** | 100只股票扩展测试 | 1-2天 | `results/performance_100stocks.txt` | ❌ 依赖E | 🔜 待启动 |

**并行策略**：
- 第1轮：Agent E + F 同时启动（2个并行）
- 第2轮：Agent G 等待E完成后启动

**Agent E任务详情**：
- 使用`AKShareProvider(adjust='qfq')`重新下载20只
- 运行`phase6d_backtest.py --full --pool medium_cap`
- 对比`results/phase6d_comparison_m0_monthly_20stocks.md`
- 记录：磁盘占用、内存峰值、回测耗时

**Agent F任务详情**：
- 分析Combo-A 2022年0持仓根因
- 打印每日过滤后的候选股票数
- 检查复权/MA/阈值问题
- 输出根因：复权 vs 阈值 vs 市场

**Agent G任务详情**：
- 回测96/100只（large_cap池）
- 记录性能指标：
  ```
  磁盘：100只 × 5年 = ? MB
  内存峰值：? MB
  下载耗时：? 分钟
  回测耗时：? 分钟
  ```

**验收标准**：
- [ ] 20只复权回测收益差异<3%
- [ ] Combo-A根因明确（复权/阈值/市场）
- [ ] 100只性能数据完整

---

### Phase 9.3: 决策评估（1-2天）

| Agent | 任务 | 耗时 | 产出 | 独立性 | 状态 |
|-------|------|------|------|--------|------|
| **Agent H** | 资源推算 | 0.5天 | `results/resource_projection.md` | ❌ 依赖G | 🔜 待启动 |
| **Agent I** | 数据源调研 | 1天 | `results/data_source_comparison.md` | ✅ 独立 | 🔜 待启动 |
| **Agent J** | 扩展决策报告 | 0.5天 | `results/expansion_decision.md` | ❌ 依赖H+I | 🔜 待启动 |

**并行策略**：
- Agent I 可随时启动（独立研究）
- Agent H 等待Phase 9.2完成
- Agent J 等待H+I完成

**Agent H任务详情**：
```markdown
基于Phase 9.2实测数据推算：
磁盘需求：100只实测 = X MB → 4000只 = X × 40 ≈ ?GB
内存需求：100只峰值 = Y MB → 4000只 = ?GB
下载时间：100只实测 = Z分钟 → 4000只 = ?小时
AKShare限流：是否可行？
```

**Agent I任务详情**：
- Tushare Pro：API限制、积分成本、除权因子质量
- AData：是否支持A股、成本
- WindAPI：企业级方案、成本
- 输出对比表

**Agent J任务详情**：
综合H+I输出决策：
- 方案A：继续AKShare（免费，限流风险）
- 方案B：购买Tushare（成本vs质量）
- 方案C：暂不扩展（专注20-96只优化）

**决策点**：
- [ ] 方案A：继续AKShare（免费）
- [ ] 方案B：购买Tushare积分
- [ ] 方案C：暂不扩展

---

### Phase 9 产出文件清单

```
Stock/
├── scripts/
│   └── verify_adjfactor.py           # Agent A
├── config/
│   └── __init__.py                   # Agent B
├── utils/
│   ├── data_provider.py              # Agent D
│   └── adjfactor.py                  # 可选（如Agent A验证失败）
├── tests/
│   └── test_smoke.py                 # Agent C
└── results/
    ├── adjfactor_verification.txt           # Agent A
    ├── phase9_20stocks_qfq_comparison.md    # Agent E
    ├── combo_a_failure_analysis.md          # Agent F
    ├── performance_100stocks.txt            # Agent G
    ├── resource_projection.md               # Agent H
    ├── data_source_comparison.md            # Agent I
    └── expansion_decision.md                # Agent J
```

**当前焦点**: Phase 9.1 已完成 ✅ (Agent A/B/C/D 全部完成，验收标准通过)

---

## 🚀 Phase 2: DataProvider 抽象层 (已完成 ✅)

**目标**: 创建统一数据接口，支持 AKShare/AData/Tushare 多数据源切换

**预计时间**: 1-1.5周 (8-12小时开发时间)
**依赖条件**: ✅ Phase 1.2 配置系统已完成

### 阶段2.1: DataProvider 抽象接口设计 (3-4小时)

**产出文件**:
- `utils/data_provider/__init__.py`
- `utils/data_provider/base.py`
- `utils/data_provider/exceptions.py`

**核心设计**:
```python
class BaseDataProvider(ABC):
    """数据提供者抽象基类"""

    @abstractmethod
    def get_stock_data(self, symbol: str, start_date: str, end_date: str,
                       adjust: str = 'qfq') -> pd.DataFrame:
        """获取股票历史数据"""
        pass

    @abstractmethod
    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指数数据（如沪深300）"""
        pass

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """验证股票代码格式"""
        pass

    @abstractmethod
    def download_to_qlib(self, symbol: str, years: int, adjust: str) -> dict:
        """下载并转换为 Qlib 格式"""
        pass
```

**关键特性**:
- 统一的数据接口（get_stock_data, get_index_data）
- 支持前复权/后复权/不复权
- 异常处理机制（DataProviderError, SymbolNotFoundError）
- 数据格式标准化（OHLCV + volume + money）
- Qlib 格式转换接口

**Agent 分配**:
- **Agent G**: 设计 `base.py` 抽象接口
- **Agent H**: 实现 `exceptions.py` 异常体系

### 阶段2.2: AKShare Provider 实现 (4-5小时)

**产出文件**:
- `utils/data_provider/akshare_provider.py`
- `tests/test_akshare_provider.py` (可选)

**实现内容**:
```python
class AKShareProvider(BaseDataProvider):
    """AKShare 数据提供者实现"""

    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)

    def get_stock_data(self, symbol: str, start_date: str, end_date: str,
                       adjust: str = 'qfq') -> pd.DataFrame:
        """从 AKShare 获取股票数据"""
        # 封装现有的 akshare.stock_zh_a_hist() 逻辑
        # 标准化输出格式
        pass

    def download_to_qlib(self, symbol: str, years: int, adjust: str) -> dict:
        """下载并保存为 Qlib CSV 格式"""
        # 封装现有的 akshare-to-qlib-converter.py 逻辑
        pass
```

**封装内容**:
- 将 `scripts/akshare-to-qlib-converter.py` 的核心逻辑提取到 Provider
- 保留原脚本作为 CLI 入口（调用 AKShareProvider）
- 添加重试机制和错误处理
- 支持数据缓存（可选优化）

**Agent 分配**:
- **Agent I**: 实现 AKShareProvider 核心逻辑
- **Agent J**: 重构 `akshare-to-qlib-converter.py` 使用新 Provider

### 阶段2.3: AData Provider 占位实现 (1-2小时)

**产出文件**:
- `utils/data_provider/adata_provider.py`

**占位实现**:
```python
class ADataProvider(BaseDataProvider):
    """AData 数据提供者（占位实现）"""

    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)

    def get_stock_data(self, symbol: str, start_date: str, end_date: str,
                       adjust: str = 'qfq') -> pd.DataFrame:
        raise NotImplementedError(
            "AData provider is not yet implemented. "
            "Please use AKShareProvider for now."
        )

    # 其他方法类似占位...
```

**Agent 分配**:
- **Agent K**: 创建 ADataProvider 占位类
- **Agent K**: 更新 `utils/data_provider/__init__.py` 导出接口

### Phase 2 并行开发策略

**第一轮并行** (3-4小时):
- Agent G + Agent H: 同时开发 base.py + exceptions.py（独立任务）

**第二轮并行** (4-5小时):
- Agent I: 开发 AKShareProvider
- Agent K: 开发 ADataProvider 占位（快速完成）
- Agent J: 等待 Agent I 完成后重构 converter 脚本

**第三轮验证** (1小时):
- 运行现有回测验证 Provider 正常工作
- 确认与 Phase 1.2 基线结果一致

### Phase 2 验收标准

| 验收项 | 标准 | 验证方法 |
|--------|------|---------|
| **接口设计** | BaseDataProvider 完整定义 | 代码审查 |
| **AKShare 实现** | 所有接口可用，数据格式正确 | 单元测试 |
| **数据一致性** | 与原始 converter 输出一致 | 对比测试 |
| **回测兼容** | phase6d_backtest 正常运行 | 完整回测 |
| **占位实现** | ADataProvider 占位类存在 | 代码审查 |

### Phase 2 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| **性能退化** | 低 | 保持原有逻辑，仅封装重构 |
| **数据格式变化** | 中 | 严格测试数据格式一致性 |
| **回测结果偏差** | 低 | 运行完整验证，对比 Phase 1.2 |
| **接口设计不足** | 中 | 预留扩展接口，支持未来数据源 |

---

## 📌 Phase 6F 止盈策略研究 (已完成)

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
