# Phase 2 部署检查清单

## ✅ 开发完成

- [x] 后端模块开发（config, selector_api, portfolio_manager, data_access）
- [x] UI组件开发（stock_table, portfolio_chart）
- [x] Streamlit页面开发（app.py, 每日选股, 模拟盘）
- [x] 文档编写（QUICK_START_STREAMLIT.md）
- [x] 测试脚本（test_streamlit_backend.py）

## 📋 用户部署步骤

### Step 1: 安装 Streamlit

由于macOS环境限制（PEP 668），需要使用虚拟环境：

```bash
# 方案A: 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install streamlit

# 方案B: 使用pipx（全局CLI工具）
brew install pipx
pipx install streamlit
```

### Step 2: 验证安装

```bash
# 运行测试脚本
python3 test_streamlit_backend.py

# 期望输出: 所有测试通过 ✓
```

### Step 3: 准备选股数据（首次必需）

```bash
# 执行一次选股，生成测试数据
python3 scripts/hs300_selector.py --budget 100000 --top 5 --skip-download
```

### Step 4: 启动 Streamlit UI

```bash
# 如果使用虚拟环境
source venv/bin/activate
streamlit run app.py

# 如果使用pipx
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`

## 🎯 验收标准

### 功能验收

- [ ] 📊 **每日选股页面**
  - [ ] 可以调整参数（预算、候选池、动量阈值）
  - [ ] 点击「执行选股」生成结果
  - [ ] 显示候选股票、持仓建议、不可负担股票
  - [ ] 可以下载CSV

- [ ] 💼 **模拟盘页面**
  - [ ] 可以创建虚拟持仓
  - [ ] 可以执行再平衡
  - [ ] 显示持仓明细和统计
  - [ ] 显示交易历史
  - [ ] 可以导出数据

- [ ] 🏠 **首页**
  - [ ] 显示系统概览
  - [ ] 显示最新选股结果
  - [ ] 显示持仓概览
  - [ ] 快速操作按钮正常

### 技术验收

- [ ] **零修改复用** - 原有脚本未被修改
- [ ] **数据统一管理** - 所有新数据写入 `data/` 目录
- [ ] **API封装** - 后端API可单独调用（不依赖Streamlit）
- [ ] **组件复用** - UI组件可在不同页面使用

## 🔧 故障排查

### 问题1: Streamlit 导入失败

```bash
# 症状: ImportError: No module named 'streamlit'
# 解决:
python3 -m venv venv
source venv/bin/activate
pip install streamlit
```

### 问题2: 选股执行失败

```bash
# 症状: 点击「执行选股」报错
# 原因: 缺少股票数据
# 解决:
python3 scripts/batch_download.py --years 3
```

### 问题3: 持仓管理失败

```bash
# 症状: 再平衡时提示「资金不足」
# 原因: 后复权价格过高
# 解决:
# 1. 增加预算金额
# 2. 或降低候选池大小
```

### 问题4: 页面显示异常

```bash
# 症状: 图表或表格显示错误
# 解决:
# 1. 刷新浏览器（Ctrl+R）
# 2. 或重启Streamlit（Ctrl+C 再 streamlit run app.py）
```

## 📈 性能指标

**目标性能**:
- 选股执行时间: <5秒（skip_download=True）
- 页面加载时间: <2秒
- 再平衡执行: <3秒

**实测性能**（待用户验证）:
- 选股: ___ 秒
- 页面加载: ___ 秒
- 再平衡: ___ 秒

## 🎯 下一步优化（可选）

Phase 2 MVP完成后，可考虑：

1. **定时任务** - Cron自动执行选股
2. **推送通知** - 企业微信/钉钉推送
3. **增强图表** - Plotly/Altair替换原生图表
4. **实盘接口** - 对接券商API

## 📞 技术支持

- 📖 使用文档: `QUICK_START_STREAMLIT.md`
- 🧪 测试脚本: `python3 test_streamlit_backend.py`
- 📋 项目说明: `CLAUDE.md`

---

**版本**: Phase 2 MVP
**完成日期**: 2025-01-10
**技术栈**: Streamlit 1.32+ / Python 3.8-3.10
**Git标签**: phase2-streamlit-ui (建议用户创建)
