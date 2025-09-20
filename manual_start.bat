@echo off
echo ===============================================
echo  CVS Pharmacy Knowledge Assist - Manual Start
echo ===============================================
echo.

cd /d "%~dp0"

echo 🚀 Starting server manually...
echo.
echo This will start the server step by step so you can see what happens.
echo.

REM Try port 8080 first
echo 🔌 Attempting to start on port 8080...
echo Command: python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
echo.
echo ⏳ Starting server... (this may take 10-15 seconds)
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8080

echo.
echo ===============================================
echo If the server started successfully, you should see:
echo "Application startup complete."
echo.
echo Then open: http://localhost:8080/static/test_main_ui.html
echo ===============================================
pause
