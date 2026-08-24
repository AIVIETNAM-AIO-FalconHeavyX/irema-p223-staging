@echo off
chcp 65001 >nul
title ⚡ Frontend — P223 (port 5173)
cd /d "%~dp0frontend"

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   🎨 Khởi chạy Frontend Vite+React   ║
echo  ║   http://localhost:5173              ║
echo  ╚══════════════════════════════════════╝
echo.

if not exist "node_modules" (
    echo [*] Cài đặt dependencies lần đầu...
    npm install
    echo.
)

echo [*] Đang khởi động frontend trên cổng 5173...
npm run dev

pause
