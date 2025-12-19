# large_cap 配置快速参考

## 当前状态
- ✅ 配置结构已就绪
- ⏳ 等待 Agent L 添加80只新增股票
- 📊 当前大小: 20只（继承自medium_cap）
- 🎯 目标大小: 100只

---

## 使用方法

```python
from config import get_settings

settings = get_settings()

# 获取 large_cap 股票池
large_cap = settings.stock_pool.get_pool('large_cap')

# 获取股票代码列表
symbols = settings.stock_pool.get_symbols('large_cap')

# 获取股票池大小
size = settings.stock_pool.get_pool_size('large_cap')
```

---

## 文件修改位置

### stock_pool.yaml
- **位置**: 第111-129行
- **修改**: 添加 `large_cap` 结构和占位符

### config/settings.py
- **StockPoolConfig**: 添加 `large_cap` 字段（第133行）
- **from_yaml()**: 添加 large_cap 继承逻辑（第182-191行）
- **get_pool()**: 移除 Literal 限制，支持动态池名（第210-232行）
- **get_pool_size()**: 新增方法（第246-255行）

---

## 验证测试

```bash
# 运行配置验证
python3 scripts/test_large_cap_config.py

# 预期输出
# ✅ 所有测试通过 (4/4)
# ⏳ 等待 Agent L 提供80只新增股票数据
```

---

## Agent L 任务

在 `stock_pool.yaml` 的 `large_cap.additional` 添加80只股票：

```yaml
large_cap:
  additional:
    - symbol: 600000.SH
      name: 浦发银行
      industry: 金融
      sector: 银行
    # ... 继续添加至80只
```

**选股标准**:
- 市值 > 100亿
- 2007年前上市
- 年均成交额 > 10亿
- 覆盖主要行业
- 数据质量良好

---

## 文档
详细文档: `/Users/elie/Downloads/Stock/docs/agent_m_large_cap_extension.md`
