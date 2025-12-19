# A股复权数据管理规范（ADJFACTOR_SPEC）
> **版本**: v1.2  
> **生效日期**: 2025-12-16  
> **适用范围**: Stock 项目全量回测与研究  
> **维护者**: Project Team  

---

## 0. 目标与范围

本规范用于统一本项目的公司行为处理、复权因子语义、对账口径与通过率统计方式，避免“口径不一致导致的隐性回测偏差”。

本规范只定义“规则/口径/验收”，不规定具体脚本实现细节。

---

## 1. 术语定义

| 术语 | 定义 | 备注 |
|------|------|------|
| `raw_*` | 不复权的原始字段（例如 `raw_close`） | 与实际交易价格一致 |
| `adjfactor` | 前复权除数（divisor），最新交易日为 `1.0` | 本项目语义锚点 |
| `adjusted_*` | 前复权价格字段（例如 `adjusted_close`） | 用于策略与对账 |
| `ak_qfq_*` | 来自 AKShare 的前复权字段 | 对账权威源 |

**核心约束**：
- 本项目中 `adjfactor` 作为除数使用：`adjusted_price = raw_price / adjfactor`
- 策略收益计算只使用 `adjusted_close`
- 回测层禁止再叠加红利现金流（否则分红被双算）

---

## 2. 复权口径与公式

### 2.1 复权类型与基准

- **复权类型**：前复权（qfq）
- **基准日期**：最新交易日 `adjfactor = 1.0`

### 2.2 价格变换（本项目定义）

- `adjusted_open  = raw_open  / adjfactor`
- `adjusted_high  = raw_high  / adjfactor`
- `adjusted_low   = raw_low   / adjfactor`
- `adjusted_close = raw_close / adjfactor`

**不复权字段**：
- `volume`、`money` 保持原值（不做复权）

### 2.3 对账等价关系（用于方向校验）

同日同股：
- `adjfactor ≈ raw_close / ak_qfq_close`

---

## 3. 数据源职责

| 数据类型 | 权威源 | 用途 |
|----------|--------|------|
| 日线价格（下载） | AKShare `stock_zh_a_hist` | 批量下载价格 |
| 前复权价格（对账） | AKShare `stock_zh_a_hist(adjust="qfq")` | 对账验证 |
| 分红/公司行为 | AData `adata.stock.market.get_dividend` | 复权因子计算 |

**约束**：
- 价格层（下载/对账/快照）统一 AKShare
- 公司行为统一 AData
- 不允许混用其它口径数据源替代上述角色（除非升级规范版本）

---

## 4. 公司行为覆盖范围

| 事件类型 | 处理方式 | 说明 |
|----------|----------|------|
| 现金分红（派息） | ✅ 自动计算 | 使用税前金额（公告口径） |
| 送股 | ✅ 自动计算 | 每股（股） |
| 转增股本 | ✅ 自动计算 | 每股（股） |
| 配股 | ⚠️ 识别但不计算 | 标记 `MANUAL_REQUIRED` |
| 拆股/并股/缩股 | ⚠️ 识别但不计算 | 标记 `MANUAL_REQUIRED` |
| 其他特殊除权 | ⚠️ 识别但不计算 | 标记 `MANUAL_REQUIRED` |

**单位约定**：
- 源数据“每10股派X元/送Y股/转Z股” → 内部统一换算为“每股”（除以10）
- `bonus/transfer` 在 `dividend_history.csv` 中存储为“每股”（股）数值

**识别来源（规则）**：
- AData `dividend_plan` 字段包含关键字：`配股`、`拆股`、`并股`、`缩股`
- 或事件类型不在 `[派息, 送股, 转增]` 枚举中

---

## 5. 回测收益口径（方案 A）

本项目采用方案 A：

- 使用 `adjusted_close` 计算收益/净值
- 回测现金流层禁止再派发红利/送转现金流（避免双算）
- 隐含假设：分红自动再投资（qfq 语义）

收益率定义（t 为交易日索引）：
- `r_t = adjusted_close(t) / adjusted_close(t-1) - 1`

---

## 6. 对账总体框架

### 6.1 日期集合定义

- `L = { d | d 出现在本地 CSV }`
- `A = { d | d 出现在 AKShare qfq 返回 }`
- `C = L ∩ A`（仅在 `C` 上进行 PASS/FAIL 判定）

### 6.2 缺失统计（独立于通过率）

- `ALIGN_MISMATCH = L \ A`（本地有、AKShare无）
- `LOCAL_MISSING  = A \ L`（本地无、AKShare有）
- `missing_rate = (|ALIGN_MISMATCH| + |LOCAL_MISSING|) / |L ∪ A|`

缺失类状态不进入通过率分母，也不计为失败，但必须在报告中单列展示。

---

## 7. 停牌与长停牌

### 7.1 停牌日判定

- `SUSPENDED(d) = (volume[d] == 0) AND (money[d] == 0)`
- 若 `money` 字段缺失，则退化为：`volume[d] == 0`

停牌日不进入通过率分母。

### 7.2 LONG_SUSPENSION

- 若连续 ≥ 30 个交易日点满足 `SUSPENDED`，则该连续区间标记为 `LONG_SUSPENSION`
- 处理规则：
  - 仅剔除该连续停牌区间内的日期点（不进通过率分母）
  - 复牌后的首个交易日点标记为 `POST_RESUME_FIRST_DAY`：
    - 不进入通过率分母
    - 单独报告（用于提醒人工关注）

---

## 8. MANUAL_REQUIRED 区间

### 8.1 区间边界定义

对于一个特殊事件（配股/拆并股/特殊除权）：
- `event_date = ex_date`
- `pre_ex = event_date 之前最近交易日`
- `post_ex = event_date 之后最近交易日`

`MANUAL_REQUIRED` 区间定义为（含端点）：
- `[pre_ex, post_ex + 20 个交易日点]`

若同一股票存在多个特殊事件区间，取区间并集。

### 8.2 统计处理

`MANUAL_REQUIRED` 区间内所有日期点：
- 不进入通过率分母
- 单独统计 `manual_coverage_rate`

---

## 9. 对账状态枚举

| 状态码 | 定义 | 入通过率分母？ | 计为失败？ |
|--------|------|----------------|------------|
| `PASS` | 通过阈值（第11章） | ✅ 是 | ❌ 否 |
| `FAIL` | 未通过阈值 | ✅ 是 | ✅ 是 |
| `ALIGN_MISMATCH` | 本地有、AKShare无 | ❌ 否 | ❌ 否（入缺失统计） |
| `LOCAL_MISSING` | 本地无、AKShare有 | ❌ 否 | ❌ 否（入缺失统计） |
| `SUSPENDED` | 停牌日 | ❌ 否 | ❌ 否 |
| `LONG_SUSPENSION` | 连续长停牌区间内日期点 | ❌ 否 | ❌ 否（单独报告） |
| `POST_RESUME_FIRST_DAY` | 复牌首日点 | ❌ 否 | ❌ 否（单独报告） |
| `MANUAL_REQUIRED` | 特殊事件区间内点 | ❌ 否 | ❌ 否（单独报告） |
| `CORE_ANCHOR_MISSING` | 锚点不在可比集合 | ❌ 否 | ❌ 否（事件级失败） |

---

## 10. 除权窗口与抽样策略

### 10.1 锚点与扩展窗口

对每个 `ex_date` 事件定义窗口：

- **锚点（必须检查）**：
  - `pre_ex`（ex_date 前最近交易日）
  - `ex_date`
  - `post_ex`（ex_date 后最近交易日）

- **扩展窗口**：
  - 在 `ex_date` 前取 5 个有效交易日点
  - 在 `ex_date` 后取 5 个有效交易日点
  - 排除：停牌点、`MANUAL_REQUIRED` 点、`LONG_SUSPENSION` 点、`POST_RESUME_FIRST_DAY` 点、锚点重复点

### 10.2 锚点缺失处理

若 `ex_date` 不在 `C`（即不在可比交集）：
- 该事件标记为 `CORE_ANCHOR_MISSING`
- 不参与自动通过率分母
- 在“按事件窗口汇总视图”中单列

---

## 11. 对账阈值与校验

### 11.1 价格阈值（AND 规则）

在有效对账集合内，对每个日期点比较：

- `local_adjusted_close = raw_close / adjfactor`
- `ak_close = ak_qfq_close`

定义：
- `abs_diff = |local_adjusted_close - ak_close|`（元）
- `rel_diff = |local_adjusted_close / ak_close - 1|`（百分比）

PASS 条件（AND）：
- `abs_diff < 0.02`
- `rel_diff < 0.1%`

### 11.2 log_return 校验（扩展窗口）

在扩展窗口内，按日期排序，逐日计算：

- `d_prev`：窗口内“上一个参与 log_return 校验的交易日点”
- `local_ratio = local_adjusted_close(d) / local_adjusted_close(d_prev)`
- `ak_ratio    = ak_close(d) / ak_close(d_prev)`
- `Δ = | ln(local_ratio) - ln(ak_ratio) |`（无量纲）

规则：
- `Δ < 0.002`（约 0.2%）
- 每个窗口允许最多 `k = 1` 个点超阈
- 锚点三点不适用 k 例外：锚点必须满足第11.1节价格阈值 AND 规则

---

## 12. 通过率与覆盖率统计

### 12.1 有效对账集合

- `effective_set = (L ∩ A) \ SUSPENDED \ MANUAL_REQUIRED \ LONG_SUSPENSION \ POST_RESUME_FIRST_DAY`

说明：
- `LONG_SUSPENSION` 指连续长停牌区间内点
- `POST_RESUME_FIRST_DAY` 指复牌首日点

### 12.2 通过率

- `pass_rate = |PASS| / |effective_set|`

### 12.3 缺失率

- `missing_rate = (|ALIGN_MISMATCH| + |LOCAL_MISSING|) / |L ∪ A|`

### 12.4 MANUAL 覆盖率

- `manual_coverage_rate = |MANUAL_REQUIRED| / N_total_points`
- `N_total_points` 为抽样后“所有尝试检查的日期点总数”（包含最终被剔除者，用于衡量人工负担）

目标建议：
- `pass_rate ≥ 99%`
- `manual_coverage_rate < 5%`

---

## 13. 报告输出要求（格式规范）

必须输出三种视图：

1) **汇总视图**
- 总点数、有效对账点数、通过点数、通过率
- 缺失统计（ALIGN_MISMATCH/LOCAL_MISSING）与缺失率
- MANUAL 覆盖率
- LONG_SUSPENSION 区间数量、POST_RESUME_FIRST_DAY 点数

2) **按股票汇总视图**
- 每只股票：有效点数、通过点数、通过率、异常状态计数（缺失/停牌/MANUAL/长停牌/复牌首日）

3) **按事件窗口汇总视图**
- 每个 `ex_date`：锚点 PASS/FAIL、窗口通过率、log_return 超阈点数、是否 `CORE_ANCHOR_MISSING`

---

## 14. 数据快照（可复现性）

### 14.1 Rolling 数据（日常研究）

- 路径：`data/with_adjfactor/*.csv`
- 该数据随更新滚动变化，用于研发与日常对账

### 14.2 Frozen 快照（回测锁定）

- 路径：`data/snapshots/{snapshot_id}/`
- `manifest.json` 进入版本控制
- 大体量数据文件默认本地化（建议 `.gitignore`）

`manifest.json` 至少包含：
- `schema_version`
- `snapshot_id`、`created_at`
- 价格数据：`source=AKShare`、`last_date`、`symbols_count`、`symbols_hash`、`file_hashes`
- 分红数据：`source=AData`、`file_hash`、`records_count`
- 依赖版本：`python_version`、`akshare_version`
- 计算脚本：`git_commit` + `calculate_adjfactor.py` 文件哈希（双保险）
- 对账产物：对账报告文件哈希（如 `results/adjfactor_audit_YYYYMMDD.csv`）

---

## 附录 A：方向校验例（完整）

测试股票：平安银行（`000001.SZ`）  
除权日：`2024-06-14`  
分红方案：10股派7.19元（每股派息 0.719 元，无送转）  

原始数据（示例）：

| 日期 | raw_close | adjfactor |
|------|----------:|----------:|
| 2024-06-13 | 9.24 | 1.161441 |
| 2024-06-14 | 9.34 | 1.077590 |

真实收益率（包含分红，t=6/13, t+1=6/14）：
- `real_return = ((1 + bonus + transfer) * close[t+1] + cash) / close[t] - 1`
- `= ((1+0+0) * 9.34 + 0.719) / 9.24 - 1`
- `= 10.059 / 9.24 - 1`
- `= +8.86%`

乘法变换（错误）：`adjusted_close = close × adjfactor`
- 6/13：`9.24 × 1.161441 = 10.7317`
- 6/14：`9.34 × 1.077590 = 10.0647`
- 调整后收益：`10.0647 / 10.7317 - 1 = −6.22%`（与真实收益差异巨大）

除法变换（正确）：`adjusted_close = close / adjfactor`
- 6/13：`9.24 / 1.161441 = 7.9556`
- 6/14：`9.34 / 1.077590 = 8.6675`
- 调整后收益：`8.6675 / 7.9556 - 1 = +8.95%`（与真实收益差异约 0.08%）

结论：本项目 `adjfactor` 必须作为除数使用。

---

## 附录 B：版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.2 | 2025-12-16 | 定稿：除数语义、对账分母、长停牌/复牌首日、MANUAL 区间、阈值与统计口径 |
