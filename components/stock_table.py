#!/usr/bin/env python3
"""
股票表格组件 - Stock Table Component

功能：
1. 候选股票表格展示
2. 持仓股票表格展示
3. 交易历史表格展示
4. 可排序、可筛选

使用示例：
    from components.stock_table import render_selection_table, render_portfolio_table

    render_selection_table(selected_stocks)
    render_portfolio_table(positions)
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional


def render_selection_table(
    stocks: List[Dict],
    show_allocation: bool = True,
    height: Optional[int] = None
):
    """
    渲染候选股票表格

    Args:
        stocks: 股票列表 [{'symbol': ..., 'name': ..., 'return_20d': ..., ...}, ...]
        show_allocation: 是否显示仓位分配信息
        height: 表格高度（像素）
    """
    if not stocks:
        st.info("📭 暂无候选股票")
        return

    # 构建DataFrame
    df = pd.DataFrame(stocks)

    # 选择显示列
    if show_allocation and 'lots' in df.columns:
        # 带仓位信息
        display_cols = ['symbol', 'name', 'close', 'return_20d', 'ma5', 'ma10', 'lots', 'cost']
        rename_map = {
            'symbol': '代码',
            'name': '名称',
            'close': '价格',
            'return_20d': '20日涨幅(%)',
            'ma5': 'MA5',
            'ma10': 'MA10',
            'lots': '手数',
            'cost': '成本(元)'
        }
    else:
        # 仅候选信息
        display_cols = ['symbol', 'name', 'close', 'return_20d', 'ma5', 'ma10']
        rename_map = {
            'symbol': '代码',
            'name': '名称',
            'close': '价格',
            'return_20d': '20日涨幅(%)',
            'ma5': 'MA5',
            'ma10': 'MA10'
        }

    # 过滤列
    display_df = df[[col for col in display_cols if col in df.columns]].copy()

    # 格式化数值
    if 'return_20d' in display_df.columns:
        display_df['return_20d'] = display_df['return_20d'] * 100  # 转为百分比

    # 重命名列
    display_df.rename(columns=rename_map, inplace=True)

    # 格式化显示
    format_dict = {
        '价格': '{:.2f}',
        '20日涨幅(%)': '{:.2f}',
        'MA5': '{:.2f}',
        'MA10': '{:.2f}'
    }

    if '成本(元)' in display_df.columns:
        format_dict['成本(元)'] = '{:.0f}'

    # 渲染表格
    st.dataframe(
        display_df.style.format(format_dict),
        use_container_width=True,
        height=height,
        hide_index=True
    )

    # 摘要信息
    st.caption(f"📊 共 {len(stocks)} 只股票")


def render_portfolio_table(
    positions: List[Dict],
    height: Optional[int] = None
):
    """
    渲染持仓表格

    Args:
        positions: 持仓列表 [{'symbol': ..., 'shares': ..., 'market_value': ..., ...}, ...]
        height: 表格高度
    """
    if not positions:
        st.info("📭 暂无持仓")
        return

    # 构建DataFrame
    df = pd.DataFrame(positions)

    # 选择显示列
    display_cols = ['symbol', 'name', 'shares', 'cost_basis', 'current_price',
                    'market_value', 'unrealized_pnl', 'unrealized_pnl_pct']

    rename_map = {
        'symbol': '代码',
        'name': '名称',
        'shares': '股数',
        'cost_basis': '成本价',
        'current_price': '当前价',
        'market_value': '市值(元)',
        'unrealized_pnl': '盈亏(元)',
        'unrealized_pnl_pct': '收益率(%)'
    }

    # 过滤列
    display_df = df[[col for col in display_cols if col in df.columns]].copy()

    # 重命名列
    display_df.rename(columns=rename_map, inplace=True)

    # 格式化显示
    format_dict = {
        '成本价': '{:.2f}',
        '当前价': '{:.2f}',
        '市值(元)': '{:.0f}',
        '盈亏(元)': '{:.2f}',
        '收益率(%)': '{:.2f}'
    }

    # 条件格式化（盈亏用颜色标记）
    def color_pnl(val):
        if pd.isna(val):
            return ''
        color = 'red' if val > 0 else 'green' if val < 0 else 'gray'
        return f'color: {color}'

    styled_df = display_df.style.format(format_dict)

    if '盈亏(元)' in display_df.columns:
        styled_df = styled_df.applymap(color_pnl, subset=['盈亏(元)'])

    if '收益率(%)' in display_df.columns:
        styled_df = styled_df.applymap(color_pnl, subset=['收益率(%)'])

    # 渲染表格
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=height,
        hide_index=True
    )

    # 摘要信息
    total_value = df['market_value'].sum() if 'market_value' in df.columns else 0
    total_pnl = df['unrealized_pnl'].sum() if 'unrealized_pnl' in df.columns else 0
    st.caption(f"📊 共 {len(positions)} 只股票 | 总市值: ¥{total_value:,.0f} | 总盈亏: ¥{total_pnl:,.2f}")


def render_trade_history_table(
    trades: List[Dict],
    limit: int = 20,
    height: Optional[int] = None
):
    """
    渲染交易历史表格

    Args:
        trades: 交易记录列表
        limit: 显示条数
        height: 表格高度
    """
    if not trades:
        st.info("📭 暂无交易记录")
        return

    # 限制条数
    display_trades = trades[:limit]

    # 构建DataFrame
    df = pd.DataFrame(display_trades)

    # 选择显示列
    base_cols = ['date', 'type', 'symbol', 'name', 'shares', 'price']

    if 'profit' in df.columns:
        display_cols = base_cols + ['cost', 'proceeds', 'profit', 'profit_pct']
        rename_map = {
            'date': '日期',
            'type': '类型',
            'symbol': '代码',
            'name': '名称',
            'shares': '股数',
            'price': '价格',
            'cost': '成本(元)',
            'proceeds': '收入(元)',
            'profit': '盈亏(元)',
            'profit_pct': '收益率(%)'
        }
    else:
        display_cols = base_cols + ['cost']
        rename_map = {
            'date': '日期',
            'type': '类型',
            'symbol': '代码',
            'name': '名称',
            'shares': '股数',
            'price': '价格',
            'cost': '成本(元)'
        }

    # 过滤列
    display_df = df[[col for col in display_cols if col in df.columns]].copy()

    # 中文化类型
    display_df['type'] = display_df['type'].map({'buy': '买入', 'sell': '卖出'})

    # 重命名列
    display_df.rename(columns=rename_map, inplace=True)

    # 格式化显示
    format_dict = {
        '价格': '{:.2f}',
        '成本(元)': '{:.0f}'
    }

    if '收入(元)' in display_df.columns:
        format_dict['收入(元)'] = '{:.0f}'
        format_dict['盈亏(元)'] = '{:.2f}'
        format_dict['收益率(%)'] = '{:.2f}'

    # 条件格式化
    styled_df = display_df.style.format(format_dict)

    def color_type(val):
        if val == '买入':
            return 'color: blue'
        elif val == '卖出':
            return 'color: orange'
        return ''

    def color_pnl(val):
        if pd.isna(val):
            return ''
        color = 'red' if val > 0 else 'green' if val < 0 else 'gray'
        return f'color: {color}'

    styled_df = styled_df.applymap(color_type, subset=['类型'])

    if '盈亏(元)' in display_df.columns:
        styled_df = styled_df.applymap(color_pnl, subset=['盈亏(元)'])

    # 渲染表格
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=height,
        hide_index=True
    )

    # 摘要信息
    buy_count = sum(1 for t in display_trades if t['type'] == 'buy')
    sell_count = sum(1 for t in display_trades if t['type'] == 'sell')
    st.caption(f"📊 共 {len(display_trades)} 笔交易 | 买入: {buy_count} | 卖出: {sell_count}")


def render_unaffordable_table(unaffordable: List[Dict], height: Optional[int] = None):
    """
    渲染不可负担股票表格

    Args:
        unaffordable: 不可负担股票列表
        height: 表格高度
    """
    if not unaffordable:
        return

    # 构建DataFrame
    df = pd.DataFrame(unaffordable)

    # 选择显示列
    display_cols = ['symbol', 'name', 'return_20d', 'price', 'min_cost', 'shortage']

    rename_map = {
        'symbol': '代码',
        'name': '名称',
        'return_20d': '20日涨幅(%)',
        'price': '价格',
        'min_cost': '1手成本(元)',
        'shortage': '资金缺口(元)'
    }

    # 过滤列
    display_df = df[[col for col in display_cols if col in df.columns]].copy()

    # 格式化数值
    if 'return_20d' in display_df.columns:
        display_df['return_20d'] = display_df['return_20d'] * 100

    # 重命名列
    display_df.rename(columns=rename_map, inplace=True)

    # 格式化显示
    format_dict = {
        '20日涨幅(%)': '{:.2f}',
        '价格': '{:.2f}',
        '1手成本(元)': '{:.0f}',
        '资金缺口(元)': '{:.0f}'
    }

    # 渲染表格
    st.dataframe(
        display_df.style.format(format_dict),
        use_container_width=True,
        height=height,
        hide_index=True
    )

    st.caption(f"⚠️ {len(unaffordable)} 只股票因预算不足被排除")
