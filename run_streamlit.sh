#!/bin/bash
# Streamlit Web UI 启动脚本

set -e

echo "========================================"
echo "  HS300 智能选股系统 - Streamlit UI"
echo "========================================"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✓ 发现虚拟环境"
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "⚠️ 未找到虚拟环境"
    echo ""
    echo "首次运行请执行以下命令创建虚拟环境："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements_streamlit.txt"
    echo ""
    exit 1
fi

# 检查Streamlit是否安装
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit 未安装"
    echo ""
    echo "请安装Streamlit："
    echo "  pip install streamlit"
    echo ""
    exit 1
fi

echo "✓ Streamlit 已安装"

# 检查是否有选股数据
if [ ! -d "data/daily" ] || [ -z "$(ls -A data/daily 2>/dev/null)" ]; then
    echo ""
    echo "⚠️ 未找到选股数据"
    echo ""
    echo "建议先执行一次选股："
    echo "  python3 scripts/hs300_selector.py --budget 100000 --top 5 --skip-download"
    echo ""
    read -p "是否现在执行选股？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "执行选股中..."
        python3 scripts/hs300_selector.py --budget 100000 --top 5 --skip-download
        echo "✓ 选股完成"
    fi
fi

echo ""
echo "========================================"
echo "  启动 Streamlit UI..."
echo "========================================"
echo ""
echo "浏览器将自动打开 http://localhost:8501"
echo ""
echo "提示："
echo "  - 按 Ctrl+C 停止服务"
echo "  - 修改代码后会自动重载"
echo ""

# 启动Streamlit
streamlit run app.py
