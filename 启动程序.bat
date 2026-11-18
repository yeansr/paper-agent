@echo off
chcp 65001 >nul
title 论文研究 Agent 启动器
cd /d "%~dp0"

echo ==========================================
echo    论文研究 Agent 启动中
echo ==========================================
echo.

REM ---- 1) 检查 Python ----
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python。
    echo 请先安装 Python 3.10 或更高版本：https://www.python.org/downloads/
    echo 安装时务必勾选 "Add Python to PATH"。
    pause
    exit /b 1
)

REM ---- 2) 检查依赖，缺失则自动安装 ----
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 首次运行，正在安装依赖，请稍候（约 2-5 分钟）...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络或换用国内镜像：
        echo   python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        pause
        exit /b 1
    )
)

REM ---- 3) 延迟几秒后用 Edge 应用模式打开（窗口无地址栏，像独立软件） ----
start "" cmd /c "timeout /t 5 /nobreak >nul & start msedge --app=http://localhost:8501"

REM ---- 4) 前台启动服务（关闭本窗口即停止服务） ----
echo.
echo 正在启动网页服务，稍后会自动弹出窗口...
echo 若未弹出，请手动打开 Edge 访问： http://localhost:8501
echo.
echo 【注意】使用期间请勿关闭本窗口，关闭会停止服务。
echo.

python -m streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false

pause
