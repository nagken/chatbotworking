@echo off
echo ========================================
echo Restarting CVS Pharmacy Knowledge Assist Server
echo ========================================
echo.
echo Stopping any running servers...

REM Kill any existing Python processes running uvicorn
taskkill /F /IM python.exe >nul 2>&1

echo.
echo Starting enhanced server with PDF text extraction...
echo Server will be available at: http://localhost:8000
echo.
echo Login credentials:
echo Email: admin@cvs-pharmacy-knowledge-assist.com
echo Password: admin123
echo.
echo Enhanced Features:
echo - Full PDF text extraction and indexing
echo - Smart document search with text snippets
echo - Contextual chat responses with document links
echo.
echo ========================================
echo.

cd /d "%~dp0"

REM Wait a moment for processes to close
timeout /t 2 /nobreak >nul

REM Start the enhanced server
echo Starting FastAPI server with enhanced PDF indexing...
"C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
