@echo off
echo ========================================
echo CVS Pharmacy Knowledge Assist - Auto Port
echo ========================================
echo.

cd /d "%~dp0"

echo Killing any existing Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo Trying different port configurations...
echo.

REM Try port 3000 first (often available)
echo Attempting port 3000...
"C:/Program Files/Python/311/python.exe" -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 3000)); print('Port 3000 available'); s.close()" 2>nul
if %errorlevel% equ 0 (
    echo Starting on port 3000...
    "C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 3000 --reload
    goto :end
)

REM Try port 5000
echo Port 3000 busy, trying port 5000...
"C:/Program Files/Python/311/python.exe" -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 5000)); print('Port 5000 available'); s.close()" 2>nul
if %errorlevel% equ 0 (
    echo Starting on port 5000...
    "C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 5000 --reload
    goto :end
)

REM Try port 9000
echo Port 5000 busy, trying port 9000...
"C:/Program Files/Python/311/python.exe" -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 9000)); print('Port 9000 available'); s.close()" 2>nul
if %errorlevel% equ 0 (
    echo Starting on port 9000...
    "C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload
    goto :end
)

echo All ports are busy! Please check running processes.
pause
exit /b 1

:end
pause
