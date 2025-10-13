# 价格修复迁移指南

## 问题说明

**修复前**（Phase 2 初始版本）:
- 使用**后复权价格(hfq)**，价格是实际交易价格的5-10倍
- 示例：真实价格 ¥50 → 显示 ¥500
- 影响：10万预算只能买1-2只股票（预算利用率15-30%）

**修复后**（当前版本）:
- 使用**真实交易价格**（无复权）
- 示例：真实价格 ¥50 → 显示 ¥50
- 效果：10万预算可买5-10只股票（预算利用率80-100%）

---

## 快速迁移（3步）

### Step 1: 验证代码已更新

确认以下文件已包含修复：

```bash
# 检查 converter 脚本（应显示 adjust="" 默认值）
grep -n "adjust=" scripts/akshare-to-qlib-converter.py

# 检查配置文件（应显示 adjust_type: ""）
grep -n "adjust_type" config.yaml
```

**预期输出**:
```
scripts/akshare-to-qlib-converter.py:103:    adjust=adjust,  # 真实交易价格（默认）
config.yaml:48:  adjust_type: ""  # 真实交易价格（默认）
```

### Step 2: 重新下载股票数据

**选项A - 使用批量下载脚本（推荐）**:

```bash
# 重新下载所有沪深300成分股（约3-5分钟）
python scripts/batch_download.py --years 3

# 提示：脚本会自动使用新的 adjust="" 配置
```

**选项B - 手动下载单只股票**:

```bash
# 下载单只股票（测试用）
python scripts/akshare-to-qlib-converter.py --symbol 000001.SZ --years 3

# 验证价格是否合理（应与交易软件一致）
head -20 ~/.qlib/qlib_data/cn_data/000001.SZ.csv
```

**选项C - 使用旧的后复权数据（不推荐）**:

```bash
# 如果需要保留后复权数据，可以指定 --adjust hfq
python scripts/akshare-to-qlib-converter.py \
  --symbol 000001.SZ \
  --years 3 \
  --adjust hfq
```

### Step 3: 验证价格修复

启动 Streamlit UI 并检查价格：

```bash
# 启动 UI
./run_streamlit.sh

# 或手动启动
source venv/bin/activate
streamlit run app.py
```

**验证检查清单**:

1. **价格显示**:
   - ✅ 价格与交易软件一致（如同花顺、东方财富）
   - ✅ 价格范围合理（大部分股票 ¥5-500 之间）
   - ❌ 不再出现 ¥1000+ 的异常高价

2. **预算利用率**:
   - ✅ 10万预算可买入 5-10 只股票
   - ✅ 预算利用率 80-100%
   - ❌ 不再出现只能买1-2只的情况

3. **持仓建议**:
   - ✅ 每只股票建议手数合理（100股的整数倍）
   - ✅ 总金额接近预算上限

---

## 数据文件位置

**Qlib 数据目录**:
```
~/.qlib/qlib_data/cn_data/
├── 000001.SZ.csv  # 平安银行
├── 000858.SZ.csv  # 五粮液
├── 600900.SH.csv  # 长江电力
└── ...            # 其他股票
```

**备份旧数据（可选）**:

```bash
# 如果需要保留旧的后复权数据，先备份
mkdir -p ~/backup_hfq_data
cp -r ~/.qlib/qlib_data/cn_data ~/backup_hfq_data/

# 然后再运行重新下载
python scripts/batch_download.py --years 3
```

---

## 常见问题

### Q1: 重新下载需要多长时间？

**A**: 取决于网络速度和股票数量：
- 单只股票：5-10秒
- 20只股票池：约2-3分钟
- 沪深300全部：约15-20分钟

### Q2: 旧数据会被覆盖吗？

**A**: 是的。`batch_download.py` 会覆盖现有的 CSV 文件。如需保留，请先备份（见上方备份命令）。

### Q3: 为什么选择"真实价格"而非"前复权"？

**A**:
- **真实价格**：与交易软件一致，便于实盘操作，价格直观
- **前复权(qfq)**：历史数据连续性好，但当前价格可能与实际不符
- **后复权(hfq)**：仅用于回测收益率计算，不适合显示

### Q4: 如果我需要计算历史收益率怎么办？

**A**: 两种方案：
1. **真实价格 + 手动复权**：在计算收益时考虑分红送股因素
2. **使用前复权数据**：下载时指定 `--adjust qfq`

### Q5: 不同复权类型的价格差异有多大？

**A**: 示例（某只股票 2025-01-10）:
```
真实价格：    ¥50.00
前复权(qfq)： ¥48.50（调整历史分红）
后复权(hfq)： ¥500.00（调整至当前基准，差异10倍）
```

---

## 技术细节

### 修改的文件

1. **scripts/akshare-to-qlib-converter.py**:
   - 添加 `adjust` 参数（默认 ""）
   - 支持命令行 `--adjust` 选项
   - 更新文档字符串

2. **config.yaml**:
   - `adjust_type: "hfq"` → `adjust_type: ""`

3. **batch_download.py** (无需修改):
   - 自动读取 config.yaml 配置
   - 使用新的默认值

### 复权类型说明

| 类型 | adjust值 | 用途 | 价格特点 |
|------|---------|------|---------|
| 真实价格 | "" | 实盘交易、价格显示 | 与交易软件一致 |
| 前复权 | "qfq" | 历史连续性分析 | 调整历史数据 |
| 后复权 | "hfq" | 收益率回测计算 | 调整至当前基准 |

---

## 完成确认

迁移完成后，请确认：

- [ ] 代码已更新（converter + config.yaml）
- [ ] 数据已重新下载（batch_download 成功）
- [ ] UI 显示价格正常（与交易软件一致）
- [ ] 预算利用率正常（80-100%）
- [ ] 持仓建议合理（5-10只股票）

---

**版本**: Phase 2 价格修复
**更新日期**: 2025-01-10
**适用范围**: 所有使用 Phase 2 Web UI 的用户

**技术支持**: 参见 README.md 或 QUICK_START_HS300.md
