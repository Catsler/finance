#!/usr/bin/env python3
"""
收益曲线组件 - Portfolio Chart Component

功能：
1. 持仓收益率曲线
2. 市值变化曲线
3. 收益分布图
4. 基于Streamlit原生图表（st.line_chart/st.bar_chart）

使用示例：
    from components.portfolio_chart import render_pnl_chart, render_value_chart

    render_pnl_chart(portfolio_history)
    render_value_chart(portfolio_history)
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime


def render_pnl_chart(
    history: List[Dict],
    title: str = "📈 收益率曲线",
    height: Optional[int] = None
):
    """
    渲染收益率曲线

    Args:
        history: 历史数据 [{'date': 'YYYY-MM-DD', 'unrealized_pnl_pct': float}, ...]
        title: 图表标题
        height: 图表高度
    """
    if not history:
        st.info("📭 暂无历史数据")
        return

    st.subheader(title)

    # 构建DataFrame
    df = pd.DataFrame(history)

    # 确保日期排序
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df.set_index('date', inplace=True)

    # 绘制收益率曲线
    if 'unrealized_pnl_pct' in df.columns:
        chart_df = df[['unrealized_pnl_pct']].copy()
        chart_df.rename(columns={'unrealized_pnl_pct': '收益率(%)'}, inplace=True)

        st.line_chart(chart_df, height=height or 400)

        # 显示摘要统计
        latest_pnl = df['unrealized_pnl_pct'].iloc[-1]
        max_pnl = df['unrealized_pnl_pct'].max()
        min_pnl = df['unrealized_pnl_pct'].min()

        col1, col2, col3 = st.columns(3)
        col1.metric("当前收益率", f"{latest_pnl:.2f}%")
        col2.metric("最高收益率", f"{max_pnl:.2f}%")
        col3.metric("最低收益率", f"{min_pnl:.2f}%")


def render_value_chart(
    history: List[Dict],
    title: str = "💰 市值变化",
    height: Optional[int] = None
):
    """
    渲染市值变化曲线

    Args:
        history: 历史数据 [{'date': 'YYYY-MM-DD', 'total_value': float, 'cash': float}, ...]
        title: 图表标题
        height: 图表高度
    """
    if not history:
        st.info("📭 暂无历史数据")
        return

    st.subheader(title)

    # 构建DataFrame
    df = pd.DataFrame(history)

    # 确保日期排序
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df.set_index('date', inplace=True)

    # 绘制市值曲线
    chart_cols = []
    rename_map = {}

    if 'total_value' in df.columns:
        chart_cols.append('total_value')
        rename_map['total_value'] = '总市值'

    if 'holdings_value' in df.columns:
        chart_cols.append('holdings_value')
        rename_map['holdings_value'] = '持仓市值'

    if 'cash' in df.columns:
        chart_cols.append('cash')
        rename_map['cash'] = '现金'

    if chart_cols:
        chart_df = df[chart_cols].copy()
        chart_df.rename(columns=rename_map, inplace=True)

        st.line_chart(chart_df, height=height or 400)

        # 显示摘要统计
        latest = df.iloc[-1]
        initial = df.iloc[0]

        col1, col2, col3 = st.columns(3)

        if 'total_value' in df.columns:
            col1.metric(
                "当前总市值",
                f"¥{latest['total_value']:,.0f}",
                f"{(latest['total_value'] - initial['total_value'])/ initial['total_value'] * 100:.2f}%"
            )

        if 'cash' in df.columns:
            col2.metric("当前现金", f"¥{latest['cash']:,.0f}")

        if 'holdings_value' in df.columns:
            col3.metric("持仓市值", f"¥{latest.get('holdings_value', 0):,.0f}")


def render_position_pie_chart(positions: List[Dict], title: str = "📊 持仓分布"):
    """
    渲染持仓分布饼图（简化版：使用柱状图）

    Args:
        positions: 持仓列表 [{'symbol': ..., 'name': ..., 'market_value': ...}, ...]
        title: 图表标题
    """
    if not positions:
        st.info("📭 暂无持仓")
        return

    st.subheader(title)

    # 构建DataFrame
    df = pd.DataFrame(positions)

    if 'market_value' not in df.columns:
        st.warning("⚠️ 数据缺少市值信息")
        return

    # 按市值排序
    df = df.sort_values('market_value', ascending=False)

    # 创建图表数据
    chart_df = df.set_index('name')[['market_value']].copy()
    chart_df.rename(columns={'market_value': '市值(元)'}, inplace=True)

    # 使用柱状图展示
    st.bar_chart(chart_df, height=400)

    # 显示占比
    total_value = df['market_value'].sum()
    st.caption("📊 持仓占比:")

    for _, row in df.iterrows():
        pct = row['market_value'] / total_value * 100
        st.caption(f"- {row['name']} ({row['symbol']}): {pct:.1f}%")


def render_summary_metrics(stats: Dict):
    """
    渲染摘要指标卡片

    Args:
        stats: 统计数据 {
            'total_value': float,
            'unrealized_pnl': float,
            'unrealized_pnl_pct': float,
            'cash': float
        }
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 总市值",
            value=f"¥{stats.get('total_value', 0):,.0f}"
        )

    with col2:
        pnl = stats.get('unrealized_pnl', 0)
        pnl_pct = stats.get('unrealized_pnl_pct', 0)
        st.metric(
            label="📈 未实现盈亏",
            value=f"¥{pnl:,.2f}",
            delta=f"{pnl_pct:.2f}%"
        )

    with col3:
        st.metric(
            label="💵 现金",
            value=f"¥{stats.get('cash', 0):,.0f}"
        )

    with col4:
        st.metric(
            label="📦 持仓市值",
            value=f"¥{stats.get('holdings_value', 0):,.0f}"
        )


def render_comparison_chart(
    selection1: Dict,
    selection2: Dict,
    title: str = "📊 选股对比"
):
    """
    渲染两次选股结果对比

    Args:
        selection1: 第一次选股结果
        selection2: 第二次选股结果
        title: 图表标题
    """
    st.subheader(title)

    # 提取Top候选
    symbols1 = {s['symbol']: s for s in selection1.get('selected', [])[:5]}
    symbols2 = {s['symbol']: s for s in selection2.get('selected', [])[:5]}

    # 构建对比数据
    all_symbols = set(symbols1.keys()) | set(symbols2.keys())

    comparison_data = []
    for symbol in all_symbols:
        s1 = symbols1.get(symbol)
        s2 = symbols2.get(symbol)

        comparison_data.append({
            '代码': symbol,
            '名称': (s1 or s2)['name'],
            f"{selection1['metadata']['date']} 涨幅(%)": (s1['return_20d'] * 100) if s1 else 0,
            f"{selection2['metadata']['date']} 涨幅(%)": (s2['return_20d'] * 100) if s2 else 0
        })

    df = pd.DataFrame(comparison_data)
    df.set_index('代码', inplace=True)

    # 显示对比柱状图
    st.bar_chart(df[[col for col in df.columns if col != '名称']], height=400)

    # 显示变化摘要
    new = set(symbols2.keys()) - set(symbols1.keys())
    removed = set(symbols1.keys()) - set(symbols2.keys())
    continued = set(symbols1.keys()) & set(symbols2.keys())

    col1, col2, col3 = st.columns(3)
    col1.metric("➕ 新增", len(new))
    col2.metric("➖ 移除", len(removed))
    col3.metric("✓ 持续", len(continued))
