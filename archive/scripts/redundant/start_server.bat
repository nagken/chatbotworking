@echo off
echo Starting PSS Knowledge Assist Server...
cd /d "c:\cvssep9"
echo Current directory: %CD%
echo.

echo Checking Python...
"C:\Program Files\Python\311\python.exe" --version
echo.

echo Checking if app can be imported...
"C:\Program Files\Python\311\python.exe" -c "from app.main import app; print(' App imported successfully')"
echo.

echo Starting server...
"C:\Program Files\Python\311\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

pause
