#!/bin/bash
# Streamlit Web UI 环境初始化脚本

set -e

echo "========================================"
echo "  HS300 智能选股系统 - 环境初始化"
echo "========================================"

# Step 1: 创建虚拟环境
echo ""
echo "[Step 1/4] 创建虚拟环境..."
if [ -d "venv" ]; then
    echo "⚠️ 虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
fi

# Step 2: 激活虚拟环境
echo ""
echo "[Step 2/4] 激活虚拟环境..."
source venv/bin/activate
echo "✓ 虚拟环境已激活"

# Step 3: 安装依赖
echo ""
echo "[Step 3/4] 安装依赖..."
echo ""
echo "安装Streamlit及相关依赖..."
pip install -r requirements_streamlit.txt
echo ""
echo "✓ 依赖安装完成"

# Step 4: 运行测试
echo ""
echo "[Step 4/4] 运行后端测试..."
echo ""
python3 test_streamlit_backend.py
echo ""

# 检查是否有选股数据
if [ ! -d "data/daily" ] || [ -z "$(ls -A data/daily 2>/dev/null)" ]; then
    echo ""
    echo "========================================"
    echo "  建议：执行首次选股"
    echo "========================================"
    echo ""
    echo "未找到选股数据，建议先执行一次选股："
    echo ""
    echo "  python3 scripts/hs300_selector.py --budget 100000 --top 5 --skip-download"
    echo ""
    read -p "是否现在执行？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "执行选股中..."
        python3 scripts/hs300_selector.py --budget 100000 --top 5 --skip-download
        echo ""
        echo "✓ 选股完成"
    fi
fi

# 完成
echo ""
echo "========================================"
echo "  ✅ 初始化完成！"
echo "========================================"
echo ""
echo "下一步："
echo ""
echo "  1. 启动 Streamlit UI："
echo "     ./run_streamlit.sh"
echo ""
echo "  或手动启动："
echo "     source venv/bin/activate"
echo "     streamlit run app.py"
echo ""
echo "  2. 浏览器访问："
echo "     http://localhost:8501"
echo ""
