#!/usr/bin/env python3
"""
实时行情页面 - Real-time Stock Quotes

功能：
1. 显示股票池实时行情
2. 核心字段：价格、涨跌幅、成交量
3. 60秒缓存，刷新按钮强制更新
"""

import streamlit as st
from utils.realtime_quote import get_realtime_quotes, clear_cache, get_stats
import pandas as pd
from datetime import datetime

# ===== YAML 加载器（ruamel 优先，PyYAML 兜底）=====
_yaml_loader = None

try:
    from ruamel.yaml import YAML as _RuamelYAML  # type: ignore

    def _load_yaml(path: str):
        loader = _RuamelYAML(typ='safe')
        with open(path, 'r', encoding='utf-8') as fh:
            return loader.load(fh)

    _yaml_loader = 'ruamel'
except ImportError:
    try:
        import yaml as _PyYAML  # type: ignore

        def _load_yaml(path: str):
            with open(path, 'r', encoding='utf-8') as fh:
                return _PyYAML.safe_load(fh)

        _yaml_loader = 'pyyaml'
    except ImportError:

        def _load_yaml(path: str):
            st.error("缺少依赖 `ruamel.yaml` 或 `PyYAML`，请运行 `pip install ruamel.yaml` 后重试。")
            st.stop()

# 页面配置
st.set_page_config(
    page_title="实时行情 - HS300系统",
    page_icon="📡",
    layout="wide"
)

# 标题
st.title("📡 实时行情")
st.markdown("显示股票池实时价格（新浪财经数据源，60秒缓存）")
st.markdown("---")

# ===== 加载股票池 =====
@st.cache_data
def load_stock_pool():
    """加载股票池配置"""
    config = _load_yaml('stock_pool.yaml')

    pools = config['stock_pools']

    # 构建 medium_cap (继承 small_cap + additional)
    symbols = []
    stock_info = {}

    # 添加 small_cap
    for stock in pools['small_cap']:
        symbols.append(stock['symbol'])
        stock_info[stock['symbol']] = stock

    # 添加 medium_cap additional
    if 'additional' in pools['medium_cap']:
        for stock in pools['medium_cap']['additional']:
            symbols.append(stock['symbol'])
            stock_info[stock['symbol']] = stock

    return symbols, stock_info

# 加载配置
symbols, stock_info = load_stock_pool()

# ===== 刷新按钮 =====
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("🔄 刷新行情", type="primary", use_container_width=True):
        clear_cache()
        st.rerun()

with col2:
    stats = get_stats()
    st.caption(f"成功率: {stats['success_rate']}")

with col3:
    st.caption("💡 提示: 数据缓存60秒，点击刷新按钮强制更新")

st.markdown("---")

# ===== 获取实时行情 =====
with st.spinner("正在获取实时行情..."):
    quotes = get_realtime_quotes(symbols, cache_seconds=60)

if not quotes:
    st.error("❌ 未能获取任何行情数据，请检查网络连接")
    st.stop()

# ===== 构建展示数据 =====
display_data = []

for quote in quotes:
    symbol = quote['symbol']
    info = stock_info.get(symbol, {})

    display_data.append({
        'symbol': symbol,
        'name': quote['name'],
        'price': quote['price'],
        'change_pct': quote['change_pct'],
        'volume': quote['volume'],
        'industry': info.get('industry', '-'),
        'sector': info.get('sector', '-'),
        'open': quote['open'],
        'high': quote['high'],
        'low': quote['low'],
        'prev_close': quote['prev_close'],
        'amount': quote['amount'],
        'timestamp': quote['timestamp'],
        'source': quote['source']
    })

df = pd.DataFrame(display_data)

# 批量格式化（减少重复代码）
formatters = {
    'price': lambda x: f'{x:.2f}',
    'change_pct': lambda x: f'+{x:.2f}%' if x > 0 else f'{x:.2f}%',
    'volume': lambda x: f'{x:,}',
    'amount': lambda x: f'{x:,.0f}'
}
for col, fmt in formatters.items():
    df[f'{col}_fmt'] = df[col].map(fmt)

# ===== 核心字段展示 =====
st.header("📊 实时行情表")

# 构建展示DataFrame（复用格式化结果）
display_df = pd.DataFrame({
    '代码': df['symbol'],
    '名称': df['name'],
    '行业': df['industry'],
    '板块': df['sector'],
    '价格(元)': df['price_fmt'],
    '涨跌幅': df['change_pct_fmt'],
    '成交量(手)': df['volume_fmt']
})

# 显示表格
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=500
)

# ===== 详细字段展开 =====
with st.expander("📋 查看详细数据"):
    st.subheader("完整行情数据")

    # 复用格式化结果
    detailed_df = pd.DataFrame({
        '代码': df['symbol'],
        '名称': df['name'],
        '现价': df['price_fmt'],
        '涨跌幅': df['change_pct_fmt'],
        '开盘': df['open'].map(lambda x: f'{x:.2f}'),
        '最高': df['high'].map(lambda x: f'{x:.2f}'),
        '最低': df['low'].map(lambda x: f'{x:.2f}'),
        '昨收': df['prev_close'].map(lambda x: f'{x:.2f}'),
        '成交量(手)': df['volume_fmt'],
        '成交额(万)': df['amount_fmt'],
        '更新时间': df['timestamp'],
        '数据源': df['source']
    })

    st.dataframe(detailed_df, use_container_width=True, hide_index=True)

    # 下载按钮
    csv = detailed_df.to_csv(index=False, encoding='utf-8-sig')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    st.download_button(
        label="📥 下载完整数据CSV",
        data=csv,
        file_name=f"realtime_quotes_{timestamp}.csv",
        mime="text/csv"
    )

st.markdown("---")

# ===== 统计信息 =====
st.header("📊 统计信息")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("股票数量", len(quotes))

with col2:
    avg_change = df['change_pct'].mean()
    st.metric("平均涨幅", f"{avg_change:+.2f}%")

with col3:
    gainers = len(df[df['change_pct'] > 0])
    st.metric("上涨数", gainers, delta=f"{gainers}/{len(quotes)}")

with col4:
    losers = len(df[df['change_pct'] < 0])
    st.metric("下跌数", losers, delta=f"{losers}/{len(quotes)}")

# ===== 涨跌排行 =====
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 涨幅榜 Top 5")
    top_gainers = df.nlargest(5, 'change_pct')[['name', 'price', 'change_pct']]

    for idx, row in top_gainers.iterrows():
        st.markdown(
            f"**{row['name']}** - ¥{row['price']:.2f} "
            f"<span style='color: red;'>+{row['change_pct']:.2f}%</span>",
            unsafe_allow_html=True
        )

with col2:
    st.subheader("📉 跌幅榜 Top 5")
    top_losers = df.nsmallest(5, 'change_pct')[['name', 'price', 'change_pct']]

    for idx, row in top_losers.iterrows():
        st.markdown(
            f"**{row['name']}** - ¥{row['price']:.2f} "
            f"<span style='color: green;'>{row['change_pct']:.2f}%</span>",
            unsafe_allow_html=True
        )

# ===== 侧边栏 =====
with st.sidebar:
    st.header("📖 功能说明")

    loader = _yaml_loader or "unknown"

    st.markdown(f"""
    ### 📡 数据来源

    - **数据源**: 新浪财经 API
    - **更新频率**: 实时（交易时段）
    - **缓存策略**: 60秒本地缓存
    - **刷新方式**: 点击"🔄 刷新行情"
    - **配置解析器**: {loader}

    ### 📊 显示字段

    **核心字段**（主表）:
    - 代码、名称、行业、板块
    - 价格、涨跌幅、成交量

    **详细字段**（展开查看）:
    - 开盘、最高、最低、昨收
    - 成交额、更新时间、数据源

    ### 🎨 颜色说明

    - <span style='color: red;'>红色</span>: 上涨
    - <span style='color: green;'>绿色</span>: 下跌
    - 黑色: 平盘

    ### ⚠️ 注意事项

    - 仅交易时段数据有效（9:30-15:00）
    - 停牌股票无法获取数据
    - 数据仅供参考，不构成投资建议
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 系统统计
    st.subheader("🔧 系统统计")
    stats = get_stats()

    st.metric("成功次数", stats['success'])
    st.metric("失败次数", stats['failure'])
    st.metric("缓存命中", stats['cache_hit'])
    st.metric("缓存未命中", stats['cache_miss'])
    st.metric("成功率", stats['success_rate'])

    # 最后更新时间
    if quotes:
        last_update = quotes[0]['timestamp']
        st.caption(f"最后更新: {last_update}")
