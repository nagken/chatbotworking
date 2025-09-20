@echo off
echo ========================================
echo PSS Knowledge Assist - Docker Stop
echo ========================================
echo.

echo Stopping PSS Knowledge Assist containers...
echo.

REM Stop Docker Compose services
docker-compose down

REM Also stop standalone container if running
docker stop pss-app 2>nul
docker rm pss-app 2>nul

echo.
echo  PSS Knowledge Assist stopped successfully!
echo.
echo To start again, use:
echo   ▶️  docker-start.bat (recommended)
echo   ▶️  docker-run.bat
echo.
pause
