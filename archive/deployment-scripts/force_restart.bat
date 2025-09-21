@echo off
echo ===============================================
echo  CVS Pharmacy - FORCE RESTART (No Reload)
echo ===============================================
echo.

cd /d "%~dp0"

echo 🛑 Killing ALL Python processes to ensure clean restart...
taskkill /F /IM python.exe 2>nul
timeout /t 3 >nul

echo 🧹 Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__ 2>nul
if exist app\__pycache__ rmdir /s /q app\__pycache__ 2>nul
if exist app\api\__pycache__ rmdir /s /q app\api\__pycache__ 2>nul
if exist app\api\routes\__pycache__ rmdir /s /q app\api\routes\__pycache__ 2>nul

echo.
echo 🚀 Starting fresh server WITHOUT reload...
echo This ensures all code changes are loaded properly.
echo.

REM Start without --reload to force fresh import
start "CVS Server - Fresh Start" cmd /k "echo CVS Pharmacy Knowledge Assist - Fresh Start && echo. && python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 && pause"

echo ⏱️ Waiting for server to start...
timeout /t 10 >nul

echo.
echo 🔍 Checking server status...
python find_server.py

echo.
echo ===============================================
echo  🎯 NOW TEST THE MAIL ORDER FIX
echo ===============================================
echo.
echo The server has been restarted WITHOUT reload mode.
echo This ensures all your code changes are active.
echo.
echo 📋 Test Steps:
echo 1. Wait for "Application startup complete" in server window
echo 2. Open: http://127.0.0.1:8080/static/index.html  
echo 3. Ask: "How do I access a member's mail order history?"
echo.
echo 🔍 Look for NEW debug messages in server logs:
echo - "Message check - contains 'mail order': True"
echo - "Using mail order history response" 
echo.
echo Press any key when ready...
pause >nul
