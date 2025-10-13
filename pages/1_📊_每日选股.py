#!/usr/bin/env python3
"""
每日选股页面 - Daily Stock Selection

功能：
1. 执行选股策略
2. 查看选股结果
3. 查看历史选股记录
"""

import streamlit as st
from datetime import datetime
from backend.selector_api import get_daily_selection
from backend.data_access import DataAccess
from backend.config import (
    DEFAULT_BUDGET,
    DEFAULT_TOP_N,
    DEFAULT_MOMENTUM_THRESHOLD,
    create_latest_link,
    get_selection_file
)
from components.stock_table import render_selection_table, render_unaffordable_table
import json

# 页面配置
st.set_page_config(
    page_title="每日选股 - HS300系统",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("📊 每日选股")
st.markdown("基于MA5/MA10动量策略筛选HS300成分股")
st.markdown("---")

# 初始化数据访问
data = DataAccess()

# ===== 参数配置 =====
st.header("⚙️ 选股参数")

col1, col2, col3 = st.columns(3)

with col1:
    budget = st.number_input(
        "总预算（元）",
        min_value=20000,
        max_value=10000000,
        value=DEFAULT_BUDGET,
        step=10000,
        help="总投资预算，最低2万元"
    )

with col2:
    top_n = st.number_input(
        "候选池大小",
        min_value=1,
        max_value=50,
        value=DEFAULT_TOP_N,
        step=1,
        help="从筛选结果中选取前N只股票"
    )

with col3:
    momentum_threshold = st.number_input(
        "动量阈值（%）",
        min_value=-20.0,
        max_value=50.0,
        value=DEFAULT_MOMENTUM_THRESHOLD,
        step=1.0,
        help="20日涨幅阈值（百分比）"
    )

# 执行选股按钮
if st.button("🚀 执行选股", type="primary", use_container_width=True):
    with st.spinner("正在执行选股策略..."):
        try:
            # 执行选股
            result = get_daily_selection(
                budget=budget,
                top_n=top_n,
                momentum_threshold=momentum_threshold / 100,  # 转为小数
                skip_download=True,
                force_refresh=False,
                silent=True
            )

            # 保存结果
            selection_date = result['metadata']['date']
            selection_file = get_selection_file(selection_date)

            with open(selection_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # 创建latest链接
            create_latest_link(selection_date)

            st.success(f"✅ 选股完成！日期: {selection_date}")

            # 缓存结果到session state
            st.session_state['latest_result'] = result

        except Exception as e:
            st.error(f"❌ 选股失败: {str(e)}")

st.markdown("---")

# ===== 选股结果展示 =====
st.header("📊 选股结果")

# 获取结果（优先使用session state，否则读取最新文件）
if 'latest_result' in st.session_state:
    result = st.session_state['latest_result']
else:
    result = data.get_latest_selection()

if result:
    # 显示元数据
    metadata = result['metadata']
    stats = result['stats']

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("选股日期", metadata['date'])
    col2.metric("成分股数", stats['constituents_count'])
    col3.metric("筛选后", f"{stats['selected_count']} 只")
    col4.metric("实际持仓", f"{stats['position_count']} 只")

    # Tab 展示
    tab1, tab2, tab3 = st.tabs(["🎯 候选股票", "💰 持仓建议", "⚠️ 不可负担"])

    with tab1:
        st.subheader("Top 候选股票（按20日涨幅排序）")
        selected = result.get('selected', [])

        if selected:
            render_selection_table(selected[:top_n], show_allocation=False, height=400)

            # 下载按钮
            csv_data = []
            for stock in selected[:top_n]:
                csv_data.append({
                    '代码': stock['symbol'],
                    '名称': stock['name'],
                    '价格': stock['close'],
                    '20日涨幅(%)': stock['return_20d'] * 100,
                    'MA5': stock['ma5'],
                    'MA10': stock['ma10']
                })

            import pandas as pd
            df = pd.DataFrame(csv_data)
            csv = df.to_csv(index=False, encoding='utf-8-sig')

            st.download_button(
                label="📥 下载候选股票CSV",
                data=csv,
                file_name=f"selection_{metadata['date']}.csv",
                mime="text/csv"
            )
        else:
            st.info("📭 无符合条件的候选股票")

    with tab2:
        st.subheader("持仓建议（等权分配）")
        allocation = result.get('allocation', {})
        positions = allocation.get('positions', [])

        if positions:
            render_selection_table(positions, show_allocation=True, height=400)

            # 显示预算利用率
            utilization = allocation.get('utilization', 0)
            total_cost = allocation.get('total_cost', 0)
            remaining = budget - total_cost

            st.progress(utilization / 100, text=f"预算利用率: {utilization:.1f}%")

            col1, col2, col3 = st.columns(3)
            col1.metric("总成本", f"¥{total_cost:,.0f}")
            col2.metric("剩余", f"¥{remaining:,.0f}")
            col3.metric("持仓数", f"{len(positions)} 只")

        else:
            st.warning("⚠️ 无可买入股票（预算不足或无符合条件标的）")

        # 显示警告
        warning = allocation.get('warning')
        if warning:
            st.warning(f"⚠️ {warning}")

    with tab3:
        st.subheader("因预算不足被排除的股票")
        allocation = result.get('allocation', {})
        unaffordable = allocation.get('unaffordable', [])

        if unaffordable:
            render_unaffordable_table(unaffordable, height=400)

            # 显示建议
            st.info(f"""
            💡 **优化建议**：
            1. 增加预算 ¥{sum(u['shortage'] for u in unaffordable):,.0f} 可买入全部 {len(unaffordable)} 只
            2. 或降低候选池大小 `--top {len(positions)}`
            """)
        else:
            st.success("✅ 所有候选股票均可负担")

else:
    st.info("📭 暂无选股数据，请先执行选股")

st.markdown("---")

# ===== 历史选股记录 =====
st.header("📚 历史选股记录")

history = data.get_selection_history(days=7)

if history:
    st.subheader(f"最近 {len(history)} 次选股")

    # 显示历史摘要
    history_data = []
    for h in history:
        meta = h['metadata']
        stats = h['stats']
        alloc = h['allocation']

        history_data.append({
            '日期': meta['date'],
            '预算': f"¥{meta['budget']:,}",
            '候选池': meta['top_n'],
            '筛选后': stats['selected_count'],
            '实际持仓': stats['position_count'],
            '预算利用率': f"{alloc.get('utilization', 0):.1f}%"
        })

    import pandas as pd
    df = pd.DataFrame(history_data)

    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("📭 暂无历史记录")

# ===== 侧边栏 =====
with st.sidebar:
    st.header("📖 策略说明")

    st.markdown("""
    ### 🎯 筛选条件

    1. **动量条件**
       - 20日涨幅 > 阈值（默认0%）

    2. **均线条件**
       - MA5 > MA10（短期均线上穿长期均线）

    ### 💰 仓位分配

    - **等权分配**: 预算 ÷ 候选数
    - **取整手数**: 1手 = 100股
    - **向下取整**: 确保不超预算

    ### ⚠️ 重要提示

    - 当前使用**后复权价格**（hfq）
    - 价格数值远高于实际交易价格
    - 导致预算利用率较低
    - **实盘需使用真实价格**

    ### 📊 数据来源

    - 成分股列表: AKShare
    - 历史数据: AKShare（后复权）
    - 缓存有效期: 7天
    """)

    st.markdown("---")

    # 快速统计
    st.subheader("📊 快速统计")

    summary = data.get_summary_stats()
    st.metric("总选股次数", summary['total_selections'])
    st.metric("最新选股", summary.get('latest_selection_date', '无') or '无')

    available_dates = data.get_available_dates()
    if available_dates:
        st.caption("最近5次:")
        for date in available_dates[:5]:
            st.caption(f"- {date}")
