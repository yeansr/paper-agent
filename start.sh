#!/bin/bash
# 论文研究 Agent 启动脚本（macOS / Linux）
cd "$(dirname "$0")"

echo "=========================================="
echo "   论文研究 Agent 启动中"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 python3，请先安装 Python 3.10+"
    exit 1
fi

# 检查依赖，缺失则安装
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "首次运行，正在安装依赖..."
    python3 -m pip install -r requirements.txt
fi

echo "启动中，稍后请在浏览器打开 http://localhost:8501"
echo "（按 Ctrl+C 可停止服务）"
echo ""

python3 -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
