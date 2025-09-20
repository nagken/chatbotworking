@echo off
echo ========================================
echo CVS Pharmacy Knowledge Assist - Alternative Port
echo ========================================
echo.

cd /d "%~dp0"

echo Checking for Python...
"C:/Program Files/Python/311/python.exe" --version
if %errorlevel% neq 0 (
    echo Error: Python not found at specified path.
    echo Please check Python installation.
    pause
    exit /b 1
)

echo.
echo Trying to kill any existing Python processes...
taskkill /F /IM python.exe >nul 2>&1

echo.
echo Starting server on port 5000 (alternative port)...
echo Server will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

"C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

pause
