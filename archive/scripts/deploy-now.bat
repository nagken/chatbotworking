@echo off
echo  PSS Knowledge Assist - Cloud Run Deploy (pbm-dev-careassist-genai-poc)
echo ======================================================================
echo.

REM Set the project
echo  Setting project: pbm-dev-careassist-genai-poc
gcloud config set project pbm-dev-careassist-genai-poc

if %errorlevel% neq 0 (
    echo  Failed to set project
    pause
    exit /b 1
)

echo  Project set successfully
echo.

REM Enable required APIs
echo  Enabling required APIs...
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --quiet

echo  APIs enabled
echo.

REM Deploy
set SERVICE_NAME=pss-knowledge-assist
set REGION=us-central1

echo  Deploying PSS Knowledge Assist to Cloud Run...
echo   � Project: pbm-dev-careassist-genai-poc
echo   �️  Service: %SERVICE_NAME%
echo   � Region: %REGION%
echo.

echo ⏱️ This may take 5-10 minutes...
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
  --set-env-vars="LOG_LEVEL=INFO,ENVIRONMENT=production,DATABASE_URL=sqlite:///app.db,SECRET_KEY=prod-secret-key-pss-2025"

if %errorlevel% neq 0 (
    echo.
    echo  Deployment failed
    echo.
    echo Common solutions:
    echo 1. Check billing is enabled for the project
    echo 2. Verify you have Cloud Run Admin permissions
    echo 3. Check internet connection
    echo 4. Try: gcloud auth login
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
    echo ⚠️ Could not retrieve service URL automatically
    echo.
    echo Please check the Cloud Console:
    echo https://console.cloud.google.com/run?project=pbm-dev-careassist-genai-poc
) else (
    echo  Service URL: %SERVICE_URL%
    echo.
    echo 🧪 Testing deployment...
    timeout /t 15 /nobreak >nul
    
    echo  PSS Knowledge Assist is live!
    echo.
    echo � PUBLIC URL: %SERVICE_URL%
    echo � Test Login: admin@pss-knowledge-assist.com / password123
    echo.
    echo  Share this URL for external testing: %SERVICE_URL%
    echo.
    echo  Monitor deployment:
    echo https://console.cloud.google.com/run/detail/%REGION%/%SERVICE_NAME%?project=pbm-dev-careassist-genai-poc
    echo.
    
    choice /c YN /m "Open application in browser? (Y/N)"
    if %errorlevel% equ 1 (
        start %SERVICE_URL%
    )
)

echo.
echo  DEPLOYMENT COMPLETE!
echo.
echo � Next steps:
echo 1. Share the URL: %SERVICE_URL%
echo 2. Test login with: admin@pss-knowledge-assist.com / password123
echo 3. Demo the chat features
echo 4. Test feedback functionality
echo.
pause
