@echo off
echo Running quick status check...
cd /d "%~dp0"
"C:/Program Files/Python/311/python.exe" quick_status_check.py
pause
