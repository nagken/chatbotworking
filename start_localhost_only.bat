@echo off
echo ========================================
echo CVS Pharmacy Knowledge Assist - Localhost Only
echo ========================================
echo.

cd /d "%~dp0"

echo Killing any existing Python processes...
taskkill /F /IM python.exe >nul 2>&1

echo.
echo Starting server on localhost:5000 (localhost binding only)...
echo Server will be available at: http://localhost:5000
echo Server will be available at: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

"C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 5000 --reload

pause
