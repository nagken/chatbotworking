@echo off
echo ========================================
echo CVS Pharmacy Knowledge Assist Server
echo ========================================
echo.
echo Starting server on http://localhost:8000
echo Use Ctrl+C to stop the server
echo.
echo Note: After server starts, open your browser to:
echo http://localhost:8000
echo.
echo Login credentials:
echo Email: admin@cvs-pharmacy-knowledge-assist.com
echo Password: admin123
echo.
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python
"C:/Program Files/Python/311/python.exe" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please ensure Python 3.11+ is installed.
    pause
    exit /b 1
)

REM Start the server
echo Starting FastAPI server...
"C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
