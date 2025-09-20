@echo off
echo  PSS Knowledge Assist - One-Click Docker Deployment
echo.

REM Check Docker
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Docker not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Clean up any existing containers
echo  Cleaning up...
docker-compose down 2>nul
docker stop pss-app 2>nul
docker rm pss-app 2>nul

REM Deploy with Docker Compose
echo  Deploying PSS Knowledge Assist...
docker-compose up --build -d

if %errorlevel% neq 0 (
    echo  Deployment failed
    pause
    exit /b 1
)

REM Wait and test
echo  Testing deployment...
timeout /t 10 /nobreak >nul
python test_docker_deployment.py

if %errorlevel% equ 0 (
    echo.
    echo  SUCCESS! PSS Knowledge Assist is running at http://localhost:8080
    start http://localhost:8080
) else (
    echo.
    echo  Deployment completed but some tests failed
    echo Check the application at http://localhost:8080
)

pause
