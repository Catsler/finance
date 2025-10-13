# 市场环境识别逻辑

## 核心指标

**20日动量** + **年化波动率**

## 判断规则

| 状态 | 条件 |
|------|------|
| 🐂 牛市 | 20日涨幅 > 5% **且** 波动率 < 15% |
| 🐻 熊市 | 20日涨幅 < -5% |
| 📊 震荡 | 其他情况 |

## 策略应用

- **熊市/震荡**：启用动态止损
- **牛市**：顺势持有（无止损）

## 使用示例

```python
from utils.market_regime import identify_market_regime

regime = identify_market_regime(hs300_data, '2023-01-31')
# 返回: 'bull', 'bear', 或 'sideways'
```

**实现位置**：`utils/market_regime.py`
