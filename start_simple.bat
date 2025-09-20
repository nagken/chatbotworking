@echo off
echo Starting CVS Pharmacy Knowledge Assist Server...
echo Current directory: %CD%

cd /d "c:\chatbotsep16"
echo Changed to: %CD%

echo.
echo Starting server on port 5000...
python -m uvicorn app.main:app --host 127.0.0.1 --port 5000

pause
