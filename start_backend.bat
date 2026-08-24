@echo off
chcp 65001 >nul
title ⚡ Backend — P223 (port 8001)
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   🚀 Khởi chạy Backend FastAPI       ║
echo  ║   http://localhost:8001/docs          ║
echo  ╚══════════════════════════════════════╝
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo ❌ Không tìm thấy .venv — hãy chạy: python -m venv .venv
    pause
    exit /b 1
)

echo [*] Đang khởi động backend trên cổng 8001...
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

pause
