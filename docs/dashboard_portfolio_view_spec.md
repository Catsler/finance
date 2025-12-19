# Dashboard Portfolio View Specification (v0.2.x Contract)

> **Goal**: Define stable UI contracts for Position/PnL display to ensure consistency between Paper Trading (v0.2.x) and future Real Trading adapters.

---

## 1. 核心字段命名契约 (Field Naming Contract)

UI 层与数据适配层必须遵守以下变量命名，严禁混用 Gross/Net。

### 1.1 成本与价格
| Field Name | Definition | Formula / Source | Notes |
|------------|------------|------------------|-------|
| `avg_cost_gross` | **不含费成本** | `positions.avg_cost` | **UI 主显成本**。A股券商通用的"持仓成本"通常不含卖出费。 |
| `avg_cost_net` | 含费净成本 | `(buy_amt + buy_fees) / qty` | *Internal use*. 仅用于计算已实现净收益回测，UI 可选展示但非核心。 |
| `last_price` | 最新价 | `quotes.last` | 实时跳动 (下单参考价另算) |
| `market_value` | 持仓市值 | `last_price * quantity` | - |

### 1.2 盈亏 (PnL)
| Field Name | Definition | Formula | Display Strategy |
|------------|------------|---------|------------------|
| `unrealized_pnl_gross` | **浮动盈亏 (未扣卖出费)** | `(last_price - avg_cost_gross) * quantity` | **UI 主显浮盈**。表头需加注 `*` (未扣卖出费用)。 |
| `unrealized_pnl_rate` | 浮动盈亏比例 | `unrealized_pnl_gross / (avg_cost_gross * total_quantity)` | 颜色区分 (+红/-绿) |
| `realized_pnl_net` | 已实现净盈亏 | Calculated by Adapter/UI | 通过重放 fills（含双边费用）计算得到。 v0.2.x暂无源字段。 |
| `today_pnl` | **今日盈亏** | `total_asset_now - total_asset_open` | 见下方详细定义 A。 |
| `accumulated_pnl` | **累计总盈亏** | `total_asset_now - initial_cash` | **UI 全局主视图**。 |

---

## 2. 核心逻辑定义

### 2.1 今日盈亏 (Method A: Snapshot)
> **Definition**: Change in total asset value since the daily open snapshot.

- **Formula**: `today_pnl = current_total_value - day_start_total_value`
- **Requirement**:
  - 后端需要一个定时任务（或懒加载逻辑），在每日开盘前（如 09:00）记录 `day_start_total_value = cash + market_value_all_positions`。
  - **Fallback**: 若无当日快照（如新启动），则 `today_pnl = 0` 或 `N/A`。
- **Why A?**: 比“持仓市值变化 + 当日已实现”更健壮，天然包含现金利息（如有）、分红到账等所有资产变动，且不受“反复做T”计算复杂度的影响。

### 2.2 股票名称源 (Name Resolution Priority)
> **Rule**: UI component resolves display name in this order:

1.  **`quote.name`**: Returns from realtime API (most accurate).
2.  **`stock_pool.yaml`**: Static mapping (fallback for known pool stocks).
3.  **`symbol`**: Raw code (last resort, e.g. "002812.SZ").

**UI Scope**: Apply to Watchlist, TradingPanel Title, Kline Chart Title/ K线图标题, Trade Record Table.

---

## 3. UI 盘面架构 (Information Architecture)

### 3.1 账户总览区 (Account Summary) -- **P0**
Layout: Top Banner
```text
[ 总资产: 4,000,000 ]  [ 现金: 450,000 ]
------------------------------------------------
[ 累计盈亏 ]       [ 今日盈亏 ]
+12,450 (+3.1%)   +1,200 (+0.3%)
(主视图)           (辅视图, 依赖快照)
```

### 3.2 持仓列表 (Position List) -- **P0**
Layout: Table / Cards
- **Columns**:
    1.  **Name/Code**: e.g., "恩捷股份 / 002812.SZ"
    2.  **Qty**: "6,700 (T+1: 6,700)" -> Show total & sellable
    3.  **Cost (Gross)**: "44.53"
    4.  **Price**: "45.00"
    5.  **PnL (Gross)* **: "+3,149" (Colorized)
    6.  **PnL %**: "+1.05%" (Colorized)
    7.  **Value**: "301,500"

### 3.3 交易面板 (Trading Panel) -- **P0 & P1**
- **Title**: Name + Code + Trend Tag (P1)
- **Trend Visual**: Trend Tag (UP/DOWN) -> Mini Daily Chart (P1)
- **Quote**: Level 1 (Bid1/Ask1/Last)
- **Trade**: Market Buy/Sell (Limit Order / Pent-level quotes pushed to P2)

---

## 4. 后续适配指引 (Adapter Guide)

未来接入实盘（如 IB / Futu / CTP）时，Adapter 层必须按上述契约输出：
- 必须转换 `unrealizedpnl` 为 **Gross** 口径（如果券商返回的是 Net，需反算或直接采用券商值但更新 UI 标注）。
- 必须自行维护或请求券商获取 `day_start_asset` 以计算 Method A 的今日盈亏。

---
**Status**: Draft for v0.2.x Implementation
**Approver**: User & Agent
**Date**: 2025-12-19
