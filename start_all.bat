@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title P223 - Start All Services
cd /d "%~dp0"

echo.
echo  +---------------------------------------------------------------+
echo  ^|          P223 - VF AI Onboarding Agent                        ^|
echo  +---------------------------------------------------------------+
echo  ^|                                                               ^|
echo  ^|  BACKEND ENDPOINTS (port 8001)                                ^|
echo  ^|  -----------------------------------------------------------  ^|
echo  ^|  Health:     http://localhost:8001/health                     ^|
echo  ^|  Swagger:    http://localhost:8001/docs                       ^|
echo  ^|  ReDoc:      http://localhost:8001/redoc                      ^|
echo  ^|  Chat API:   http://localhost:8001/api/v1/chat                ^|
echo  ^|  Auth:       http://localhost:8001/api/v1/auth/login          ^|
echo  ^|  Files:      http://localhost:8001/api/v1/files/{path}        ^|
echo  ^|  S3 Files:   http://localhost:8001/api/v1/s3-files/{key}      ^|
echo  ^|  S3 Manager: http://localhost:8001/api/v1/s3-manager/explore  ^|
echo  ^|  Test UI:    http://localhost:8001/api/v1/test_input           ^|
echo  ^|  Ingest:     http://localhost:8001/api/v1/ingest              ^|
echo  ^|  Feedback:   http://localhost:8001/api/v1/feedback            ^|
echo  ^|                                                               ^|
echo  ^|  FRONTEND (port 5173)                                         ^|
echo  ^|  -----------------------------------------------------------  ^|
echo  ^|  Web App:    http://localhost:5173                             ^|
echo  ^|                                                               ^|
echo  ^|  DOCKER SERVICES                                              ^|
echo  ^|  -----------------------------------------------------------  ^|
echo  ^|  PostgreSQL: localhost:5432                                    ^|
echo  ^|  MinIO API:  http://localhost:9000                             ^|
echo  ^|  MinIO Web:  http://localhost:9001  (minioadmin/minioadmin)    ^|
echo  ^|  Langfuse:   http://localhost:3000                             ^|
echo  ^|  ClamAV:     localhost:3310                                    ^|
echo  ^|                                                               ^|
echo  +---------------------------------------------------------------+
echo.

:: ---------------------------------------------------------------
:: 1. Docker Services
:: ---------------------------------------------------------------
echo --- [1/3] Docker Services ---
docker info >nul 2>&1
if !errorlevel! neq 0 (
    echo   [SKIP] Docker Desktop chua chay - bo qua MinIO/DB/Langfuse
    echo.
    goto start_backend
)

echo   Dang khoi dong Docker services...
docker compose up -d s3 db langfuse clamav 2>nul
timeout /t 4 /nobreak >nul

echo.
echo   Kiem tra tinh trang Docker:

set "DB_STATUS=[STOP]"
set "S3_STATUS=[STOP]"
set "LF_STATUS=[STOP]"
set "AV_STATUS=[STOP]"

for /f "tokens=*" %%i in ('docker ps --format "{{.Names}}" 2^>nul') do (
    echo %%i | findstr /i "db postgres" >nul 2>&1 && set "DB_STATUS=[ OK ]"
    echo %%i | findstr /i "s3 minio" >nul 2>&1 && set "S3_STATUS=[ OK ]"
    echo %%i | findstr /i "langfuse" >nul 2>&1 && set "LF_STATUS=[ OK ]"
    echo %%i | findstr /i "clamav" >nul 2>&1 && set "AV_STATUS=[ OK ]"
)

echo   !DB_STATUS! PostgreSQL   :5432
echo   !S3_STATUS! MinIO        :9000 / :9001
echo   !LF_STATUS! Langfuse     :3000
echo   !AV_STATUS! ClamAV       :3310
echo.

:: ---------------------------------------------------------------
:: 2. Backend
:: ---------------------------------------------------------------
:start_backend
echo --- [2/3] Backend (FastAPI + Uvicorn) ---

if not exist ".venv\Scripts\activate.bat" (
    echo   [FAIL] .venv khong tim thay! Chay: python -m venv .venv
    echo.
    goto start_frontend
)

echo   Dang khoi dong Backend tren port 8001...
start "Backend_P223" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && uvicorn src.main:app --reload --host 0.0.0.0 --port 8001"
echo   [ OK ] Backend dang khoi dong (cua so rieng)
echo          Cho 10-15s de load AI models, sau do truy cap:
echo          http://localhost:8001/health
echo          http://localhost:8001/docs
echo.

:: ---------------------------------------------------------------
:: 3. Frontend
:: ---------------------------------------------------------------
:start_frontend
echo --- [3/3] Frontend (Vite + React) ---

if not exist "frontend\node_modules" (
    echo   Cai dat npm dependencies lan dau...
    pushd "%~dp0frontend"
    npm install
    popd
    echo.
)

echo   Dang khoi dong Frontend tren port 5173...
start "Frontend_P223" cmd /k "cd /d %~dp0frontend && npm run dev"
echo   [ OK ] Frontend dang khoi dong (cua so rieng)
echo          http://localhost:5173
echo.

:: ---------------------------------------------------------------
:: Summary
:: ---------------------------------------------------------------
echo ---------------------------------------------------------------
echo   Tat ca da khoi chay! Ctrl+Click de mo link phia tren.
echo   De dung: dong cac cua so Backend va Frontend.
echo ---------------------------------------------------------------
echo.
pause
