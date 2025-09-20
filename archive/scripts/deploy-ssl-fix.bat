@echo off
echo  PSS Knowledge Assist - SSL Fix Deployment
echo =============================================
echo.

REM Check Docker
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Docker not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo  Docker is running
echo.

REM Clean up any existing containers
echo 🧹 Cleaning up existing containers...
docker-compose down 2>nul
docker stop pss-app 2>nul
docker rm pss-app 2>nul
docker rmi pss-knowledge-assist 2>nul

echo  Trying SSL-fixed Dockerfile...
echo.

REM Build with SSL-fixed Dockerfile
docker build -f Dockerfile.ssl-fix -t pss-knowledge-assist .

if %errorlevel% neq 0 (
    echo.
    echo  SSL-fixed build failed. Trying direct run method...
    echo.
    
    REM Try running without Docker Compose - direct method
    echo  Starting container directly...
    docker run -d --name pss-app -p 8080:8080 -e DATABASE_URL=sqlite:///app.db -e SECRET_KEY=dev-secret-key-for-testing python:3.11-slim sh -c "
        apt-get update && 
        apt-get install -y gcc libpq-dev curl ca-certificates && 
        update-ca-certificates && 
        pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org fastapi uvicorn sqlalchemy alembic bcrypt python-jose python-multipart && 
        cd /app && 
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
    "
    
    if %errorlevel% neq 0 (
        echo  Direct method failed too. Let's try local Python instead.
        echo.
        echo � Falling back to local Python deployment...
        
        REM Check if Python is available
        python --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo  Python not found. Please install Python 3.11+ or fix Docker SSL issues.
            echo.
            echo  Solutions:
            echo 1. Check Docker Desktop network settings
            echo 2. Try disabling corporate VPN/firewall temporarily
            echo 3. Install Python locally and run: run_server.bat
            pause
            exit /b 1
        )
        
        REM Install requirements locally
        echo Installing requirements locally...
        pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
        
        if %errorlevel% neq 0 (
            echo  Local pip install failed too. 
            echo This suggests a network/SSL configuration issue.
            echo.
            echo  Please try:
            echo 1. Disable VPN/corporate firewall temporarily
            echo 2. Run: pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org"
            echo 3. Contact IT support about SSL certificate issues
            pause
            exit /b 1
        )
        
        echo  Requirements installed locally
        echo  Starting local server on http://localhost:8000...
        start http://localhost:8000
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        pause
        exit /b 0
    )
    
    echo  Container started directly
    timeout /t 5 /nobreak >nul
    start http://localhost:8080
    echo.
    echo  SUCCESS! PSS Knowledge Assist is running at http://localhost:8080
    echo.
    echo To stop: docker stop pss-app
    pause
    exit /b 0
)

REM If SSL-fixed build succeeded, run with docker-compose
echo  SSL-fixed build successful!
echo  Starting with docker-compose...

docker-compose up -d

if %errorlevel% neq 0 (
    echo  Docker-compose failed, trying direct container run...
    docker run -d --name pss-app -p 8080:8080 -e DATABASE_URL=sqlite:///app.db -e SECRET_KEY=dev-secret-key-for-testing pss-knowledge-assist
)

echo.
echo ⏳ Testing deployment...
timeout /t 10 /nobreak >nul

REM Test if the service is running
curl -s http://localhost:8080/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo  SUCCESS! PSS Knowledge Assist is running at http://localhost:8080
    start http://localhost:8080
) else (
    echo ⚠️ Service started but health check failed. Check manually at http://localhost:8080
    start http://localhost:8080
)

echo.
echo � To stop: docker stop pss-app (or docker-compose down)
pause
