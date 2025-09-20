@echo off
echo ========================================
echo PSS Knowledge Assist - Docker Compose
echo ========================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Docker is not running or not installed
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

echo  Docker is running
echo.

echo Starting PSS Knowledge Assist with Docker Compose...
echo.

docker-compose up --build -d

if %errorlevel% neq 0 (
    echo  Docker Compose failed
    pause
    exit /b 1
)

echo.
echo  PSS Knowledge Assist is starting up!
echo.
echo The application will be available at:
echo    http://localhost:8080
echo    http://127.0.0.1:8080
echo.
echo ⏳ Waiting for application to be ready...

REM Wait for application to be ready
:check_health
timeout /t 3 /nobreak >nul
curl -s http://localhost:8080/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo   ... still starting up
    goto check_health
)

echo.
echo  Application is ready!
echo.
echo  Container status:
docker-compose ps
echo.
echo � To view logs: docker-compose logs -f
echo � To stop: docker-compose down
echo  To restart: docker-compose restart
echo.
echo Opening application in browser...
start http://localhost:8080
echo.
pause
