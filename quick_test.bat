@echo off
echo Testing CVS Pharmacy Document Search...
echo.

echo 1. Testing if server is running...
curl -s http://127.0.0.1:8080/api/health
echo.
echo.

echo 2. Testing document search (no auth required)...
curl -s "http://127.0.0.1:8080/api/documents/search?query=mail+order+history"
echo.
echo.

echo Test complete!
pause
