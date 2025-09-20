@echo off
echo Stopping any existing Python processes...
taskkill /F /IM python.exe >nul 2>&1

echo Waiting 3 seconds...
timeout /t 3 >nul

echo Starting PSS Knowledge Assist server...
echo Server will run on http://localhost:8080
echo.
echo Available endpoints:
echo   - Main app: http://localhost:8080/
echo   - Test login: http://localhost:8080/test-login
echo   - Debug test: http://localhost:8080/debug-test  
echo   - Health check: http://localhost:8080/health
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "c:\cvssep9"
"C:\Program Files\Python\311\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

pause
