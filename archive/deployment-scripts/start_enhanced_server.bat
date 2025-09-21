@echo off
echo Starting CVS Pharmacy Knowledge Assist server...
cd /d c:\chatbotsep16
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
