@echo off
echo  PSS Knowledge Assist - Quick Start
echo =====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python not found. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo  Python found
echo.

REM Try different ports to find an available one
set PORT=8001

echo  Finding available port...

REM Check if port 8001 is available
netstat -an | findstr ":8001 " >nul
if %errorlevel% equ 0 (
    set PORT=8002
    echo Port 8001 busy, trying 8002...
)

REM Check if port 8002 is available
netstat -an | findstr ":8002 " >nul
if %errorlevel% equ 0 (
    set PORT=8003
    echo Port 8002 busy, trying 8003...
)

REM Check if port 8003 is available
netstat -an | findstr ":8003 " >nul
if %errorlevel% equ 0 (
    set PORT=8004
    echo Port 8003 busy, trying 8004...
)

echo  Using port %PORT%
echo.

echo  Checking requirements...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing FastAPI and dependencies...
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org fastapi uvicorn sqlalchemy alembic bcrypt python-jose python-multipart requests
)

echo  Requirements ready
echo.

echo  Starting PSS Knowledge Assist on http://localhost:%PORT%...
echo.

REM Start the browser
start http://localhost:%PORT%

REM Start the server
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload
