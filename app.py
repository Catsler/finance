#!/usr/bin/env python3
"""
HS300 智能选股系统 - Streamlit Web UI

主入口：系统概览页面

运行方式：
    streamlit run app.py
"""

import streamlit as st
from datetime import datetime
from backend.data_access import DataAccess
from components.stock_table import render_selection_table, render_portfolio_table
from components.portfolio_chart import render_summary_metrics

# 页面配置
st.set_page_config(
    page_title="HS300 智能选股系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📈 HS300 智能选股系统")
st.markdown("---")

# 初始化数据访问
data = DataAccess()

# ===== 系统概览 =====
st.header("🏠 系统概览")

# 获取摘要统计
summary = data.get_summary_stats()

# 显示指标卡片
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📊 选股记录",
        value=f"{summary['total_selections']} 次"
    )

with col2:
    latest_date = summary.get('latest_selection_date', '-')
    st.metric(
        label="📅 最新选股日期",
        value=latest_date if latest_date else "暂无"
    )

with col3:
    has_portfolio = "✅ 已创建" if summary['has_portfolio'] else "❌ 未创建"
    st.metric(
        label="💼 虚拟持仓",
        value=has_portfolio
    )

with col4:
    st.metric(
        label="🔄 总交易数",
        value=f"{summary['total_trades']} 笔"
    )

st.markdown("---")

# ===== 最新选股 =====
st.header("📊 最新选股结果")

latest_selection = data.get_latest_selection()

if latest_selection:
    # 显示元数据
    metadata = latest_selection.get('metadata', {})
    stats = latest_selection.get('stats', {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("选股日期", metadata.get('date', '-'))
    col2.metric("预算", f"¥{metadata.get('budget', 0):,}")
    col3.metric("候选池", f"{metadata.get('top_n', 0)} 只")
    col4.metric("实际持仓", f"{stats.get('position_count', 0)} 只")

    # 显示候选股票
    st.subheader("🎯 Top 候选股票")
    selected = latest_selection.get('selected', [])
    render_selection_table(selected[:10], show_allocation=False, height=300)

    # 显示持仓建议
    st.subheader("💰 持仓建议")
    allocation = latest_selection.get('allocation', {})
    positions = allocation.get('positions', [])

    if positions:
        render_selection_table(positions, show_allocation=True, height=250)

        # 显示预算利用率
        utilization = allocation.get('utilization', 0)
        st.progress(utilization / 100, text=f"预算利用率: {utilization:.1f}%")
    else:
        st.warning("⚠️ 无可买入股票（预算不足或无符合条件标的）")

    # 显示警告信息
    warning = allocation.get('warning')
    if warning:
        st.warning(f"⚠️ {warning}")

else:
    st.info("📭 暂无选股数据，请前往「每日选股」页面执行选股")

st.markdown("---")

# ===== 持仓概览 =====
st.header("💼 持仓概览")

if summary['has_portfolio']:
    # 获取持仓统计
    portfolio_stats = data.get_portfolio_stats()

    # 显示摘要指标
    render_summary_metrics(portfolio_stats)

    # 显示持仓明细
    st.subheader("📊 持仓明细")
    positions = portfolio_stats.get('positions', [])

    if positions:
        render_portfolio_table(positions, height=300)
    else:
        st.info("📭 当前无持仓")

else:
    st.info("📭 暂无持仓数据，请前往「模拟盘」页面创建虚拟持仓")

st.markdown("---")

# ===== 快速操作 =====
st.header("⚡ 快速操作")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 执行今日选股", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📊_每日选股.py")

with col2:
    if st.button("💼 查看模拟盘", use_container_width=True):
        st.switch_page("pages/2_💼_模拟盘.py")

with col3:
    if st.button("🔄 刷新数据", use_container_width=True):
        st.rerun()

# ===== 侧边栏 =====
with st.sidebar:
    st.header("📖 使用指南")

    st.markdown("""
    ### 🚀 快速开始

    1. **每日选股** - 执行选股策略，获取候选股票
    2. **模拟盘** - 创建虚拟持仓，跟踪收益表现
    3. **月度再平衡** - 每月调整持仓，模拟Phase 6D策略

    ### 📊 系统特性

    - ✅ 动量策略筛选（MA5/MA10 + 20日涨幅）
    - ✅ 等权仓位分配
    - ✅ 月度再平衡
    - ✅ 本地JSON持久化
    - ✅ 零修改复用现有脚本

    ### ⚠️ 注意事项

    - 当前使用**后复权价格**（hfq），价格高于实际
    - 适合策略验证，实盘需调整为真实价格
    - 数据来源：AKShare（免费数据源）

    ---

    **版本**: Phase 2 MVP
    **更新**: {datetime.now().strftime('%Y-%m-%d')}
    """)

    st.markdown("---")

    # 系统状态
    st.subheader("🔧 系统状态")

    status_items = [
        ("📊 数据访问", "✅ 正常" if data.get_available_dates() else "⚠️ 无数据"),
        ("💼 持仓管理", "✅ 正常" if summary['has_portfolio'] else "⚠️ 未初始化"),
        ("🔄 最新记录", summary.get('latest_selection_date', '无') or '无')
    ]

    for label, value in status_items:
        st.caption(f"{label}: {value}")
