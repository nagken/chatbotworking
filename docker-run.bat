@echo off
echo ========================================
echo PSS Knowledge Assist - Docker Runner
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

REM Stop and remove existing container if it exists
echo Cleaning up existing container...
docker stop pss-app 2>nul
docker rm pss-app 2>nul

echo.
echo Starting PSS Knowledge Assist...
echo.

docker run -d -p 8080:8080 --name pss-app pss-knowledge-assist

if %errorlevel% neq 0 (
    echo  Failed to start container
    echo.
    echo Trying to build the image first...
    call docker-build.bat
    echo.
    echo Starting container again...
    docker run -d -p 8080:8080 --name pss-app pss-knowledge-assist
    
    if %errorlevel% neq 0 (
        echo  Still failed to start container
        pause
        exit /b 1
    )
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
docker ps --filter name=pss-app --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo � To view logs: docker logs -f pss-app
echo � To stop: docker stop pss-app
echo  To restart: docker restart pss-app
echo.
echo Opening application in browser...
start http://localhost:8080
echo.
pause
