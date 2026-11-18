#!/bin/bash
# ============================================================
# 一键启动：Streamlit + Cloudflare 公网隧道
# 用途：把网页版 Agent 暴露成手机可打开的 https 临时链接
# 运行：bash start_public.sh
# ============================================================

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
mkdir -p logs

echo "[1/3] 启动 Streamlit 网页服务..."
nohup python3 -m streamlit run app.py \
    --server.address 0.0.0.0 --server.port 8501 \
    --server.headless true --browser.gatherUsageStats false \
    > logs/streamlit.log 2>&1 &

# 等待本地服务就绪（最多 25 秒）
for i in $(seq 1 25); do
    if curl -s -o /dev/null --max-time 2 http://localhost:8501/; then
        echo "      网页服务已就绪"
        break
    fi
    sleep 1
done

echo "[2/3] 建立 Cloudflare 隧道..."
nohup tools/cloudflared tunnel --url http://localhost:8501 --no-autoupdate \
    > logs/tunnel.log 2>&1 &

# 等待分配公网域名（最多 25 秒）
PUBLIC_URL=""
for i in $(seq 1 25); do
    PUBLIC_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" logs/tunnel.log | head -1)
    if [ -n "$PUBLIC_URL" ]; then
        break
    fi
    sleep 1
done

echo "[3/3] 完成"
echo "$PUBLIC_URL" > logs/public_url.txt
echo ""
echo "============================================"
echo " 手机访问地址：$PUBLIC_URL"
echo "============================================"
