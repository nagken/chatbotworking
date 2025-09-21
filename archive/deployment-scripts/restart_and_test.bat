@echo off
echo ===============================================
echo  CVS Pharmacy - Restart Server & Test Fix
echo ===============================================
echo.

cd /d "%~dp0"

echo 🛑 Stopping any running servers...
echo.

REM Kill any existing uvicorn processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq CVS Server*" 2>nul
timeout /t 2 >nul

echo 🚀 Starting CVS Pharmacy server with fixes...
echo.
echo ⏳ Please wait for "Application startup complete" message...
echo.

REM Start server in new window
start "CVS Server - Mail Order Fix" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload && pause"

echo ⏱️ Waiting for server to start...
timeout /t 8 >nul

echo.
echo 🔍 Checking if server is ready...
python find_server.py

echo.
echo ===============================================
echo  🎯 TEST THE MAIL ORDER HISTORY FIX
echo ===============================================
echo.
echo 📋 Next Steps:
echo.
echo 1. Wait for server startup to complete
echo 2. Open: http://127.0.0.1:8080/static/index.html
echo 3. Login: john.smith@cvshealth.com / password123
echo 4. Ask: "How do I access a member's mail order history?"
echo.
echo 🔍 Expected Results:
echo - Enhanced response mentioning specific document
echo - "📚 Related Documents Found" section
echo - Debug logs showing "mail order history response"
echo.
echo 📊 Alternative Test Query:
echo - Ask: "What is contraceptive coverage?"
echo.
echo ===============================================
echo  🌐 Test URLs (once server is ready)
echo ===============================================
echo.
echo Main Chat UI:   http://127.0.0.1:8080/static/index.html
echo Test Interface: http://127.0.0.1:8080/static/test_main_ui.html
echo Debug Tool:     http://127.0.0.1:8080/static/chat_debug.html
echo Health Check:   http://127.0.0.1:8080/api/health
echo API Docs:       http://127.0.0.1:8080/docs
echo.
echo Press any key when ready to test...
pause >nul
