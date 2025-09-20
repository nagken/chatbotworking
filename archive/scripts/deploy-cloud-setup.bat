@echo off
echo  PSS Knowledge Assist - Google Cloud Run Setup & Deploy
echo ========================================================
echo.

REM Check if gcloud is installed
gcloud version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Google Cloud CLI not found
    echo Please install from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo  Google Cloud CLI found
echo.

REM Check authentication
gcloud auth list --filter=status:ACTIVE --format="value(account)" >nul 2>&1
if %errorlevel% neq 0 (
    echo  Please authenticate with Google Cloud...
    gcloud auth login
    if %errorlevel% neq 0 (
        echo  Authentication failed
        pause
        exit /b 1
    )
)

echo  Authenticated with Google Cloud
echo.

REM Get current project
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i

if "%PROJECT_ID%"=="" (
    echo  No project set. Let's set one up...
    echo.
    
    REM Show available projects
    echo Available projects:
    gcloud projects list --format="table(projectId,name,projectNumber)"
    echo.
    
    set /p PROJECT_ID="Enter project ID (or press Enter to create new): "
    
    if "%PROJECT_ID%"=="" (
        echo � Creating new project...
        set PROJECT_ID=pss-knowledge-assist-%RANDOM%
        
        gcloud projects create %PROJECT_ID% --name="PSS Knowledge Assist"
        if %errorlevel% neq 0 (
            echo  Failed to create project
            pause
            exit /b 1
        )
        
        echo  Project created: %PROJECT_ID%
    )
    
    gcloud config set project %PROJECT_ID%
    if %errorlevel% neq 0 (
        echo  Failed to set project
        pause
        exit /b 1
    )
)

echo  Using project: %PROJECT_ID%
echo.

REM Check billing (required for Cloud Run)
echo � Checking billing status...
gcloud billing projects describe %PROJECT_ID% >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Billing not enabled for this project
    echo.
    echo Please enable billing:
    echo 1. Go to: https://console.cloud.google.com/billing/linkedaccount?project=%PROJECT_ID%
    echo 2. Link a billing account (free tier available)
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo  Billing enabled
echo.

REM Enable required APIs
echo  Enabling required APIs...
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --quiet
if %errorlevel% neq 0 (
    echo ⚠️ Failed to enable APIs, continuing anyway...
)

echo  APIs enabled
echo.

REM Deploy
set SERVICE_NAME=pss-knowledge-assist
set REGION=us-central1

echo  Deploying PSS Knowledge Assist to Cloud Run...
echo   � Project: %PROJECT_ID%
echo   �️  Service: %SERVICE_NAME%
echo   � Region: %REGION%
echo.

echo This may take 5-10 minutes...
echo.

gcloud run deploy %SERVICE_NAME% ^
  --source . ^
  --region %REGION% ^
  --platform managed ^
  --allow-unauthenticated ^
  --port 8080 ^
  --memory 1Gi ^
  --cpu 1 ^
  --max-instances 10 ^
  --set-env-vars="LOG_LEVEL=INFO,ENVIRONMENT=production,DATABASE_URL=sqlite:///app.db" ^
  --quiet

if %errorlevel% neq 0 (
    echo.
    echo  Deployment failed
    echo.
    echo Common solutions:
    echo 1. Ensure billing is enabled
    echo 2. Check internet connection  
    echo 3. Try: gcloud auth application-default login
    echo 4. Check project permissions
    pause
    exit /b 1
)

echo.
echo  Deployment successful!
echo.

REM Get the service URL
echo  Getting service URL...
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)" 2^>nul') do set SERVICE_URL=%%i

if "%SERVICE_URL%"=="" (
    echo ⚠️ Could not retrieve service URL
    echo Check: https://console.cloud.google.com/run?project=%PROJECT_ID%
) else (
    echo  Service URL: %SERVICE_URL%
    echo.
    echo 🧪 Testing deployment...
    timeout /t 10 /nobreak >nul
    
    curl -f -s "%SERVICE_URL%/api/health" >nul 2>&1
    if %errorlevel% equ 0 (
        echo  Health check passed
        echo.
        echo  PSS Knowledge Assist is live!
        echo.
        echo � Public URL: %SERVICE_URL%
        echo � Test Login: admin@pss-knowledge-assist.com / password123
        echo.
        echo  Monitor: https://console.cloud.google.com/run/detail/%REGION%/%SERVICE_NAME%?project=%PROJECT_ID%
        echo.
        
        choice /c YN /m "Open application in browser? (Y/N)"
        if %errorlevel% equ 1 (
            start %SERVICE_URL%
        )
    ) else (
        echo ⚠️ Health check failed - service might still be starting
        echo Try: %SERVICE_URL%
    )
)

echo.
echo � Your app is now deployed to Google Cloud Run!
echo � Share this URL for testing: %SERVICE_URL%
echo.
pause
