# Dashboard v0.2 Implementation Plan (60分K + KDJ)

**定位**：服务当前 60分K + KDJ 低频策略的“信号触发后人工确认/干预”看盘界面；不做全功能同花顺/东方财富。

---

## 1. 目标与非目标

### 目标（v0.2）
- 60分K 主图 + VOL + KDJ 副图（ECharts）
- 叠加成交点（基于 `/api/v1/fills`）与持仓成本线（基于 `/api/v1/positions`）
- 支持十字光标、缩放拖拽、前复权（qfq）切换
- 轮询刷新：适配“信号触发才打开看 1-2 只”，兼容偶尔长挂

### 非目标（v0.2 不做）
- WebSocket 实时推送、L2 五档深度、回放模式、多股分屏、画线工具
- IndexedDB/本地持久缓存、无限历史加载（先用 400 根窗口）

---

## 2. 关键约定（必须遵守）

### 2.1 时间语义：`candles.time = bar_end_time`
- `candles[].time` 表示该根 K 线的**结束时间**（ISO，CN 时区语义）。
- 60m bar_end_time 序列（A股交易时段）通常为：`10:30, 11:30, 14:00, 15:00`（午休跳空是正常的）。
- 该约定与 `utils/kdj_rules.KdjSignal.bar_end_time` / `is_1500_bar(bar_end_time_iso)` 一致。

### 2.2 成交点映射：`fill.trade_time -> 最早一个 candle_end >= fill_time`
当 `candles.time` 是 bar_end_time 时：
- 用“**最早一个 `candle.time >= fill.trade_time`**”确定成交标记落点。
- 例：candle_end=[10:30, 11:30, 14:00, 15:00]，fill_time=11:15 ⇒ 映射到 11:30（对应 10:30–11:30 这根K线）。

### 2.3 未完成K线过滤：默认只返回“已完成 60m bar”
- `/api/v1/candles` 默认 `include_incomplete=false`。
- 后端需在 CN 时区下计算 `last_complete_time`，并过滤 `candle.time <= last_complete_time`。

---

## 3. 轮询与数据窗口（v0.2 定版）

| 数据 | 频率 | 说明 |
|---|---:|---|
| Quotes `/api/v1/quotes` | 10–15s | 信号触发场景足够 |
| Account/Positions/Orders/Fills/Events | 15s | 执行后刷新及时 |
| 60m Candles `/api/v1/candles` | 60s | 每小时才新增一根；v0.2 可先全量拉 400 根 |

窗口：
- `limit=400`（约 50 个交易日）
- v0.2 不做“加载更多历史”，不做 IndexedDB

---

## 4. 后端 API 设计（Paper Trading FastAPI）

### 4.1 P0：`GET /api/v1/candles`

参数：
- `symbol`: `000001.SZ`
- `tf`: 固定 `60m`（v0.2 仅支持该值）
- `adjust`: `front|none|back`（映射 AKShare：`qfq|''|hfq`）
- `limit`: 默认 400
- `include_incomplete`: 默认 false

响应（建议字段）：
```json
{
  "symbol": "000001.SZ",
  "tf": "60m",
  "adjust": "front",
  "last_complete_time": "2025-12-18T14:00:00",
  "candles": [
    {"time":"2025-12-18T10:30:00","open":1,"high":1,"low":1,"close":1,"volume":1}
  ]
}
```

实现提示：
- 数据源：AKShare `stock_zh_a_hist_min_em(period="60")`
- `candles.time` 需对齐为 bar_end_time（必要时做标准化/重采样）
- `last_complete_time` 用于前端判断“是否有新完成K线”

### 4.2 P1：`GET /api/v1/trend/daily`

目标：前端只展示“日线趋势 UP/DOWN/FLAT”，并用于策略 gate（后续落到策略侧）。

参数建议：
- `symbol`
- `ma=20`
- `lookback=5`
- `adjust=front`

响应建议：
```json
{"symbol":"000001.SZ","ma":20,"lookback":5,"trend":"UP","ma_last":12.34,"slope":0.012}
```

trend 判定建议：
- 用 `MA20` 在 `lookback` 窗口的斜率 `slope`（或末值差）做阈值分类，避免抖动：
  - `slope > +eps => UP`
  - `slope < -eps => DOWN`
  - else `FLAT`

---

## 5. 前端实现（React + Antd + ECharts）

### 5.1 组件结构（P0）
- 新增图表组件：`frontend/src/components/KlineKdjChart.jsx`
- Dashboard 里的“占位卡片”替换为真实图表组件（按当前 `activeSymbol` 渲染）

### 5.2 KDJ 算法一致性（P0）
必须与 `kdj_strategy/indicators.calculate_kdj()` 一致（`adjust=False`）。

伪代码（EWMA，alpha=1/3）：
```text
RSV[i] = ((close - LLV9) / (HHV9 - LLV9)) * 100
RSV[i] 缺失 -> 50

K[0] = RSV[0]
K[i] = alpha*RSV[i] + (1-alpha)*K[i-1]

D[0] = K[0]
D[i] = alpha*K[i] + (1-alpha)*D[i-1]

J[i] = 3*K[i] - 2*D[i]
```

注意：
- 不要使用 `adjust=True` 的实现（会与 pandas 结果偏离）
- 数据不足（<9）时 RSV 会被填 50，K/D 会逐步收敛

### 5.3 成交点与成本线（P0）
来源：
- 成交点：`/api/v1/fills`
- 成本线：`/api/v1/positions` 的 `avg_cost`（仅持仓>0显示）

成交点 tooltip（建议）：
- `direction/price/quantity/trade_time`
- `fees_total = commission + stamp_tax + transfer_fee`
- `realized_pnl`：前端按平均成本法“重放 fills”计算（v0.2 不改后端 DB）

平均成本重放规则（与撮合逻辑一致）：
- BUY：`new_avg = (qty*avg + fill_qty*price) / (qty + fill_qty)`
- SELL：avg_cost 不变；`realized_pnl = (price - avg_cost) * fill_qty - fees_total`

---

## 6. 执行顺序（建议）
1. 后端：实现 `/api/v1/candles`（含 `last_complete_time` + 完成K线过滤）
2. 前端：实现 `KlineKdjChart.jsx`（K线 + VOL + KDJ + 交互）
3. 前端：叠加 fills 成交标记 + positions 成本线 + tooltip
4. 后端（P1）：实现 `/api/v1/trend/daily`
5. 前端（P1）：TradingPanel/图表标题展示 `daily_trend`
6. 分时图（P1）：如仍需要，再追加

---

## 7. 验收标准（v0.2）
- 选中股票后 3 秒内完成图表渲染（首屏拉 400 根 60m）
- KDJ 数值与策略侧计算一致（抽样对比 3–5 个时间点）
- 成交点在正确的 60m bar 上（按 bar_end_time 映射规则）
- 成本线与 `/api/v1/positions.avg_cost` 一致
