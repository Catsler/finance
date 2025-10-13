#!/usr/bin/env python3
"""
模拟盘页面 - Virtual Portfolio

功能：
1. 创建/重置虚拟持仓
2. 月度再平衡
3. 持仓统计与收益跟踪
4. 交易历史查看
"""

import streamlit as st
from datetime import datetime
from backend.portfolio_manager import VirtualPortfolio
from backend.data_access import DataAccess
from backend.config import DEFAULT_BUDGET
from components.stock_table import render_portfolio_table, render_trade_history_table
from components.portfolio_chart import render_summary_metrics, render_position_pie_chart

# 页面配置
st.set_page_config(
    page_title="模拟盘 - HS300系统",
    page_icon="💼",
    layout="wide"
)

# 标题
st.title("💼 虚拟持仓")
st.markdown("模拟真实交易，跟踪收益表现")
st.markdown("---")

# 初始化
data = DataAccess()

# ===== 持仓管理 =====
st.header("⚙️ 持仓管理")

col1, col2, col3 = st.columns(3)

with col1:
    # 创建/重置持仓
    if st.button("🆕 创建新持仓", use_container_width=True):
        initial_cash = st.session_state.get('initial_cash', DEFAULT_BUDGET)

        portfolio = VirtualPortfolio(initial_cash=initial_cash, load_existing=False)
        portfolio.reset(cash=initial_cash)

        st.success(f"✅ 创建成功！初始资金: ¥{initial_cash:,}")
        st.rerun()

with col2:
    # 月度再平衡
    if st.button("🔄 执行再平衡", type="primary", use_container_width=True):
        if data.has_portfolio():
            # 获取最新选股结果
            latest = data.get_latest_selection()

            if latest:
                allocation = latest['allocation']
                positions = allocation.get('positions', [])

                if positions:
                    # 执行再平衡
                    portfolio = VirtualPortfolio(load_existing=True)
                    rebalance_date = datetime.now().strftime('%Y-%m-%d')

                    try:
                        portfolio.rebalance(positions, date=rebalance_date)
                        st.success(f"✅ 再平衡完成！日期: {rebalance_date}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 再平衡失败: {str(e)}")
                else:
                    st.warning("⚠️ 最新选股无可买入股票")
            else:
                st.warning("⚠️ 请先执行选股")
        else:
            st.warning("⚠️ 请先创建持仓")

with col3:
    # 重置持仓
    if st.button("🗑️ 重置持仓", use_container_width=True):
        if data.has_portfolio():
            portfolio = VirtualPortfolio(load_existing=True)
            portfolio.reset(cash=DEFAULT_BUDGET)
            st.success("✅ 持仓已重置")
            st.rerun()
        else:
            st.warning("⚠️ 暂无持仓可重置")

# 初始资金设置
with st.expander("⚙️ 高级设置"):
    initial_cash = st.number_input(
        "初始资金（元）",
        min_value=20000,
        max_value=10000000,
        value=DEFAULT_BUDGET,
        step=10000,
        help="创建新持仓时的初始资金"
    )
    st.session_state['initial_cash'] = initial_cash

st.markdown("---")

# ===== 持仓概览 =====
if data.has_portfolio():
    st.header("📊 持仓概览")

    # 获取持仓统计
    stats = data.get_portfolio_stats()

    # 显示摘要指标
    render_summary_metrics(stats)

    st.markdown("---")

    # Tab 展示
    tab1, tab2, tab3 = st.tabs(["📦 持仓明细", "📈 持仓分布", "🔄 交易历史"])

    with tab1:
        st.subheader("持仓明细")
        positions = stats.get('positions', [])

        if positions:
            render_portfolio_table(positions, height=400)

            # 下载按钮
            import pandas as pd

            csv_data = []
            for p in positions:
                csv_data.append({
                    '代码': p['symbol'],
                    '名称': p['name'],
                    '股数': p['shares'],
                    '成本价': p['cost_basis'],
                    '当前价': p['current_price'],
                    '市值': p['market_value'],
                    '盈亏': p['unrealized_pnl'],
                    '收益率(%)': p['unrealized_pnl_pct']
                })

            df = pd.DataFrame(csv_data)
            csv = df.to_csv(index=False, encoding='utf-8-sig')

            st.download_button(
                label="📥 下载持仓明细CSV",
                data=csv,
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        else:
            st.info("📭 当前无持仓")

    with tab2:
        st.subheader("持仓分布")

        if positions:
            render_position_pie_chart(positions)
        else:
            st.info("📭 当前无持仓")

    with tab3:
        st.subheader("交易历史")

        # 限制条数
        limit = st.slider("显示记录数", 10, 100, 20, 10)

        trades = data.get_trade_history(limit=limit)

        if trades:
            render_trade_history_table(trades, limit=limit, height=400)

            # 下载按钮
            import pandas as pd

            df = pd.DataFrame(trades[:limit])
            csv = df.to_csv(index=False, encoding='utf-8-sig')

            st.download_button(
                label="📥 下载交易历史CSV",
                data=csv,
                file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        else:
            st.info("📭 暂无交易记录")

    st.markdown("---")

    # ===== 收益分析 =====
    st.header("📈 收益分析")

    # 近期表现摘要
    perf = data.get_performance_summary(days=30)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("近30天交易", f"{perf['total_trades']} 笔")
    col2.metric("已实现盈亏", f"¥{perf['realized_pnl']:,.2f}")
    col3.metric("胜率", f"{perf['win_rate']:.1f}%")
    col4.metric("买入/卖出", f"{perf['buy_count']}/{perf['sell_count']}")

else:
    st.info("📭 暂无持仓数据，请先创建虚拟持仓")

# ===== 侧边栏 =====
with st.sidebar:
    st.header("📖 使用说明")

    st.markdown("""
    ### 🚀 快速开始

    1. **创建持仓**
       - 点击「创建新持仓」
       - 设置初始资金（默认10万）

    2. **执行再平衡**
       - 先在「每日选股」页面执行选股
       - 返回此页点击「执行再平衡」
       - 系统自动清仓旧持仓，买入新持仓

    3. **查看表现**
       - 持仓明细：当前持股情况
       - 交易历史：所有买卖记录
       - 收益分析：盈亏统计

    ### 💡 月度再平衡逻辑

    遵循 **Phase 6D** 策略：

    1. **清仓**: 卖出所有现有持仓
    2. **重新买入**: 根据最新选股结果等权配置
    3. **频率**: 建议每月执行一次

    ### ⚠️ 注意事项

    - 价格数据来自Qlib（后复权）
    - 如果股票数据缺失，使用成本价
    - 虚拟盘仅供策略验证，非实盘交易
    - 交易记录保存在 `data/portfolio/`

    ### 📊 数据说明

    - **未实现盈亏**: 当前持仓的账面盈亏
    - **已实现盈亏**: 卖出股票的实际盈亏
    - **收益率**: 盈亏 ÷ 成本
    - **胜率**: 盈利交易 ÷ 总交易
    """)

    st.markdown("---")

    # 快速统计
    st.subheader("📊 快速统计")

    if data.has_portfolio():
        summary = data.get_summary_stats()

        st.metric("持仓总市值", f"¥{summary['portfolio_value']:,.0f}")
        st.metric("总交易数", summary['total_trades'])

        # 最近交易
        recent_trades = data.get_trade_history(limit=3)
        if recent_trades:
            st.caption("最近3笔交易:")
            for t in recent_trades:
                type_emoji = "🔵" if t['type'] == 'buy' else "🟠"
                st.caption(f"{type_emoji} {t['date']} {t['symbol']} {t['shares']}股")
    else:
        st.info("暂无持仓数据")
