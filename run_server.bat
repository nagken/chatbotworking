@echo off
echo ========================================
echo PSS Knowledge Assist - Server Startup
echo ========================================
echo.

cd /d "c:\cvssep9"
echo Starting server on port 8000...
echo.
echo The application will be available at:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
