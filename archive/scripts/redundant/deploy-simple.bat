quick-start.batquick-start.bat@echo off
echo  PSS Knowledge Assist - Simple Local Deployment
echo ================================================
echo.

REM Try Python first (fastest option)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo  Python found - using local deployment
    echo.
    echo  Installing requirements...
    
    REM Install with trusted hosts to avoid SSL issues
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org fastapi uvicorn sqlalchemy alembic bcrypt python-jose python-multipart requests
    
    if %errorlevel% equ 0 (
        echo  Requirements installed
        echo  Starting PSS Knowledge Assist on http://localhost:8001...
        echo.
        start http://localhost:8001
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
        pause
        exit /b 0
    ) else (
        echo ⚠️ Pip install had issues, but continuing...
    )
)

echo.
echo ⚠️ Python not found or pip install failed
echo � Trying Docker with SSL workarounds...
echo.

REM Check Docker
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Docker also not available
    echo.
    echo  Please install either:
    echo 1. Python 3.11+ and run: pip install fastapi uvicorn
    echo 2. Docker Desktop
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

echo  Docker found
echo.

REM Clean up
echo 🧹 Cleaning up...
docker stop pss-app 2>nul
docker rm pss-app 2>nul

REM Try a minimal Docker approach without building our Dockerfile
echo � Running minimal Docker container...
docker run -d ^
  --name pss-app ^
  -p 8082:8000 ^
  -v "%cd%":/app ^
  -w /app ^
  -e PIP_TRUSTED_HOST=pypi.org,pypi.python.org,files.pythonhosted.org ^
  python:3.11-slim ^
  sh -c "pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org fastapi uvicorn sqlalchemy alembic bcrypt python-jose python-multipart requests && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

if %errorlevel% equ 0 (
    echo  Container started
    echo ⏳ Waiting for startup...
    timeout /t 15 /nobreak >nul
    echo.
    echo  SUCCESS! PSS Knowledge Assist should be running at:
    echo    http://localhost:8082
    echo.
    start http://localhost:8082
    echo � To stop: docker stop pss-app
) else (
    echo  Docker run failed
    echo.
    echo  SSL/Network issues detected. Try these solutions:
    echo.
    echo 1. **Disable VPN/Corporate Firewall temporarily**
    echo 2. **Check Docker Desktop network settings**
    echo 3. **Run on a different network** (mobile hotspot, home wifi)
    echo 4. **Contact IT support** about PyPI access
    echo.
    echo Alternative: Install Python locally and run:
    echo    pip install fastapi uvicorn
    echo    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
)

pause
