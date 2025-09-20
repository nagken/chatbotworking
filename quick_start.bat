@echo off
echo ===============================================
echo  CVS Pharmacy Knowledge Assist - Quick Start
echo ===============================================
echo.

cd /d "%~dp0"

echo 🔍 Checking if server is already running...
python find_server.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ No server found - will start one now...
    goto :start_server
) else (
    echo.
    echo ✅ Server found! Use the URLs shown above to test.
    echo.
    echo 🧪 Running quick test...
    python test_nonstreaming_endpoint.py
    echo.
    echo 🌐 Opening test interface...
    timeout /t 2 >nul
    start "" "http://localhost:8080/static/test_main_ui.html"
    pause
    exit /b 0
)

:start_server

echo.
echo 🚀 Starting CVS Pharmacy server...
echo Will try ports 8080, 5000, 3000 until one works...
echo.

REM Try port 8080 first
echo Trying port 8080...
start "CVS Server" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8080"
timeout /t 8 >nul

echo Checking if server started on 8080...
python find_server.py
if %errorlevel% equ 0 goto :server_started

echo Trying port 5000...
start "CVS Server Port 5000" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 5000"
timeout /t 8 >nul

python find_server.py
if %errorlevel% equ 0 goto :server_started

echo ❌ Could not start server automatically.
echo.
echo 📋 Manual startup:
echo   python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
echo.
pause
exit /b 1

:server_started
echo.
echo ✅ Server started successfully!
echo.
echo 🧪 Running automated tests...
python test_nonstreaming_endpoint.py

echo.
echo 🌐 Opening test interface in browser...
timeout /t 3 >nul

REM Find the correct port and open test UI
for /f "tokens=*" %%i in ('python find_server.py ^| findstr "Test UI"') do (
    for /f "tokens=3" %%j in ("%%i") do start "" "%%j"
)

echo.
echo ===============================================
echo  🎉 CVS Pharmacy Knowledge Assist Ready!
echo ===============================================
echo.
echo ✅ Server running and tested
echo ✅ Browser opened with test interface
echo.
echo 📋 Test the fixes:
echo 1. Login: john.smith@cvshealth.com / password123  
echo 2. Ask: "What is contraceptive coverage?"
echo 3. Look for "📚 Related Documents Found" section
echo 4. Check browser console (F12) for debug messages
echo.
echo Press any key to continue...
pause >nul
