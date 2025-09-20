@echo off
echo Starting CVS Pharmacy Knowledge Assist...
echo.
echo Configuration:
echo - Server will start on http://localhost:8000
echo - PDF documents will be indexed from GyaniNuxeo folder
echo - Login credentials: admin@cvs-pharmacy-knowledge-assist.com / admin123
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install requirements if needed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting server...
echo Open your browser to http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
