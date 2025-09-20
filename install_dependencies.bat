@echo off
echo ========================================
echo CVS Pharmacy Knowledge Assist - Setup
echo ========================================
echo.

cd /d "%~dp0"

echo Installing required Python packages...
echo This may take a few minutes...
echo.

REM Upgrade pip first
"C:/Program Files/Python/311/python.exe" -m pip install --upgrade pip

REM Install specific packages that might be missing
echo Installing PDF processing packages...
"C:/Program Files/Python/311/python.exe" -m pip install PyPDF2==3.0.1
"C:/Program Files/Python/311/python.exe" -m pip install python-docx==0.8.11

REM Install all requirements
echo Installing all requirements...
"C:/Program Files/Python/311/python.exe" -m pip install -r requirements.txt

echo.
echo Installation complete!
echo.
echo Now you can start the server with:
echo   start_localhost_only.bat
echo.
pause
