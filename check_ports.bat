@echo off
echo ========================================
echo CVS Pharmacy Knowledge Assist - Port Checker
echo ========================================
echo.

echo Checking what's using port 8000...
netstat -ano | findstr :8000
echo.

echo Checking what's using port 8080...
netstat -ano | findstr :8080
echo.

echo Checking for Python processes...
tasklist | findstr python.exe
echo.

echo Available alternative ports to try:
echo - Port 3000
echo - Port 5000
echo - Port 7000
echo - Port 9000
echo.

pause
