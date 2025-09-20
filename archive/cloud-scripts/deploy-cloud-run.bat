@echo off
echo  PSS Knowledge Assist - Google Cloud Run Deployment
echo ========================================================
echo.

REM Check if gcloud is installed
gcloud version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Google Cloud CLI not found
    echo.
    echo Please install the Google Cloud CLI:
    echo https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo  Google Cloud CLI is available
echo.

REM Get current project
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i

if "%PROJECT_ID%"=="" (
    echo  No Google Cloud project set
    echo.
    echo Please set your project:
    echo   gcloud config set project YOUR_PROJECT_ID
    echo.
    echo Or list available projects:
    echo   gcloud projects list
    pause
    exit /b 1
)

echo  Current project: %PROJECT_ID%
echo.

REM Enable required APIs
echo  Enabling required Google Cloud APIs...
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable containerregistry.googleapis.com --quiet

if %errorlevel% neq 0 (
    echo ⚠️ Failed to enable some APIs, continuing anyway...
)

echo.

REM Set deployment variables
set SERVICE_NAME=pss-knowledge-assist
set REGION=us-central1
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

echo  Deploying PSS Knowledge Assist to Cloud Run...
echo   � Project: %PROJECT_ID%
echo   �️  Service: %SERVICE_NAME%
echo   � Region: %REGION%
echo   � Image: %IMAGE_NAME%
echo.

REM Option 1: Deploy from source (simpler)
echo  Building and deploying from source...
gcloud run deploy %SERVICE_NAME% ^
  --source . ^
  --region %REGION% ^
  --platform managed ^
  --allow-unauthenticated ^
  --port 8080 ^
  --memory 512Mi ^
  --cpu 1 ^
  --max-instances 10 ^
  --set-env-vars="LOG_LEVEL=INFO,ENVIRONMENT=production,DEBUG_MODE=false" ^
  --quiet

if %errorlevel% neq 0 (
    echo.
    echo  Deployment failed
    echo.
    echo Common solutions:
    echo   1. Check your internet connection
    echo   2. Verify billing is enabled on your project
    echo   3. Ensure you have Cloud Run Admin permissions
    echo   4. Try: gcloud auth login
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
    echo Check the Cloud Console for your service URL
) else (
    echo  Service URL: %SERVICE_URL%
    echo.
    echo 🧪 Testing deployment...
    
    REM Wait a moment for deployment to be ready
    timeout /t 10 /nobreak >nul
    
    REM Test the health endpoint
    curl -f -s "%SERVICE_URL%/api/health" >nul 2>&1
    if %errorlevel% equ 0 (
        echo  Health check passed
        echo.
        echo  PSS Knowledge Assist is live!
        echo � Share this URL with testers: %SERVICE_URL%
        echo.
        echo  Monitor your service:
        echo   https://console.cloud.google.com/run/detail/%REGION%/%SERVICE_NAME%
        echo.
        
        REM Open in browser
        choice /c YN /m "Open application in browser? (Y/N)"
        if %errorlevel% equ 1 (
            start %SERVICE_URL%
        )
    ) else (
        echo ⚠️ Health check failed - service might still be starting
        echo Check logs: gcloud logs read "resource.type=cloud_run_revision" --limit 20
    )
)

echo.
echo � Useful commands:
echo   View logs:     gcloud logs read "resource.type=cloud_run_revision" --limit 50
echo   Update env:    gcloud run services update %SERVICE_NAME% --region %REGION% --set-env-vars="KEY=value"
echo   Delete:        gcloud run services delete %SERVICE_NAME% --region %REGION%
echo   List services: gcloud run services list
echo.
pause
