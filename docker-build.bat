@echo off
echo ========================================
echo PSS Knowledge Assist - Docker Builder
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

echo Building PSS Knowledge Assist Docker image...
echo.

docker build -t pss-knowledge-assist .

if %errorlevel% neq 0 (
    echo  Docker build failed
    pause
    exit /b 1
)

echo.
echo  Docker image built successfully!
echo.
echo You can now run the application with:
echo   docker run -p 8080:8080 --name pss-app pss-knowledge-assist
echo.
echo Or use docker-compose:
echo   docker-compose up -d
echo.
pause
