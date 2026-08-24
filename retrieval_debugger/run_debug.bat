@echo off
title VinFast AI Retrieval Debugger
chcp 65001 > nul
cd /d "%~dp0.."

echo =========================================================================
echo    VF AI ONBOARDING - RAG RETRIEVAL TESTING & DEBUGGING FRAMEWORK
echo =========================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [1] Chạy toàn bộ (Canary Test + Ground Truth Dataset - End-to-End với LLM)
echo [2] Chạy chế độ nhanh (Retrieval-Only, không tốn token LLM)
echo [3] Chỉ chạy Unique Canary Test
echo [4] Tự nhập câu hỏi kiểm thử tùy chỉnh
echo.
set /p choice="Chọn chế độ (1-4, mặc định là 1): "

if "%choice%"=="2" (
    "%PYTHON_EXE%" retrieval_debugger/run_debug.py --retrieval-only
) else if "%choice%"=="3" (
    "%PYTHON_EXE%" retrieval_debugger/run_debug.py --canary-only
) else if "%choice%"=="4" (
    set /p custom_query="Nhập câu hỏi cần debug: "
    set /p custom_role="Nhập vai trò (sales/accounting/technician/general): "
    "%PYTHON_EXE%" retrieval_debugger/run_debug.py --query "%custom_query%" --role "%custom_role%"
) else (
    "%PYTHON_EXE%" retrieval_debugger/run_debug.py
)

echo.
echo =========================================================================
echo    Hoàn tất kiểm thử! Báo cáo đã được lưu trong thư mục reports/
echo =========================================================================
pause
