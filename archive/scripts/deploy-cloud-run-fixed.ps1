# PSS Knowledge Assist - Google Cloud Run Deployment
# Project: pbm-dev-careassist-genai-poc

Write-Host " PSS Knowledge Assist - Google Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Project configuration
$PROJECT_ID = "pbm-dev-careassist-genai-poc"
$SERVICE_NAME = "pss-knowledge-assist"
$REGION = "us-central1"

# Check if gcloud is installed
Write-Host " Checking Google Cloud CLI..." -ForegroundColor Yellow
try {
    $gcloudVersion = gcloud version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud not found"
    }
    Write-Host " Google Cloud CLI found" -ForegroundColor Green
} catch {
    Write-Host " Google Cloud CLI not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Google Cloud CLI:" -ForegroundColor Yellow
    Write-Host "https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Set project
Write-Host " Setting project: $PROJECT_ID" -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host " Failed to set project" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host " Project set successfully" -ForegroundColor Green
Write-Host ""

# Check authentication
Write-Host " Checking authentication..." -ForegroundColor Yellow
$authAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($authAccount)) {
    Write-Host " Please authenticate with Google Cloud..." -ForegroundColor Yellow
    gcloud auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Host " Authentication failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host " Authenticated successfully" -ForegroundColor Green
Write-Host ""

# Enable required APIs
Write-Host " Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Warning: Failed to enable some APIs, continuing anyway..." -ForegroundColor Yellow
} else {
    Write-Host " APIs enabled successfully" -ForegroundColor Green
}
Write-Host ""

# Deploy to Cloud Run
Write-Host " Deploying PSS Knowledge Assist to Cloud Run..." -ForegroundColor Cyan
Write-Host "   � Project: $PROJECT_ID" -ForegroundColor White
Write-Host "   �️  Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "   � Region: $REGION" -ForegroundColor White
Write-Host ""
Write-Host "⏱️ This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

# Environment variables for deployment
$envVars = "LOG_LEVEL=INFO,ENVIRONMENT=production,DATABASE_URL=sqlite:///app.db,SECRET_KEY=prod-secret-pss-2025"

# Deploy command
gcloud run deploy $SERVICE_NAME `
  --source . `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --memory 1Gi `
  --cpu 1 `
  --max-instances 10 `
  --set-env-vars=$envVars `
  --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host " Deployment failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "1. Check billing is enabled for the project" -ForegroundColor White
    Write-Host "2. Verify you have Cloud Run Admin permissions" -ForegroundColor White
    Write-Host "3. Check internet connection" -ForegroundColor White
    Write-Host "4. Try: gcloud auth application-default login" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host " Deployment successful!" -ForegroundColor Green
Write-Host ""

# Get service URL
Write-Host " Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project $PROJECT_ID 2>$null

if ([string]::IsNullOrEmpty($serviceUrl)) {
    Write-Host "⚠️ Could not retrieve service URL automatically" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please check the Cloud Console:" -ForegroundColor Yellow
    Write-Host "https://console.cloud.google.com/run?project=$PROJECT_ID" -ForegroundColor Cyan
} else {
    Write-Host " Service URL: $serviceUrl" -ForegroundColor Green
    Write-Host ""
    
    # Test deployment
    Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Write-Host " PSS Knowledge Assist is live!" -ForegroundColor Green
    Write-Host ""
    Write-Host "� PUBLIC URL: $serviceUrl" -ForegroundColor Cyan
    Write-Host "� Test Login: admin@pss-knowledge-assist.com / password123" -ForegroundColor White
    Write-Host ""
    Write-Host " Share this URL for external testing: $serviceUrl" -ForegroundColor Cyan
    Write-Host ""
    
    # Monitor links
    Write-Host " Monitor deployment:" -ForegroundColor Yellow
    Write-Host "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME" + "?project=$PROJECT_ID" -ForegroundColor Cyan
    Write-Host ""
    
    # Ask to open browser
    $openBrowser = Read-Host "Open application in browser? (Y/N)"
    if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
        Start-Process $serviceUrl
    }
}

Write-Host ""
Write-Host " DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "� Next steps:" -ForegroundColor Yellow
Write-Host "1. Share the URL: $serviceUrl" -ForegroundColor White
Write-Host "2. Test login with: admin@pss-knowledge-assist.com / password123" -ForegroundColor White
Write-Host "3. Demo the chat features" -ForegroundColor White
Write-Host "4. Test feedback functionality" -ForegroundColor White
Write-Host ""

# Useful commands
Write-Host " Useful commands:" -ForegroundColor Yellow
Write-Host "View logs:     gcloud logs read 'resource.type=cloud_run_revision' --limit 50 --project $PROJECT_ID" -ForegroundColor White
Write-Host "Update env:    gcloud run services update $SERVICE_NAME --region $REGION --set-env-vars='KEY=value' --project $PROJECT_ID" -ForegroundColor White
Write-Host "Delete:        gcloud run services delete $SERVICE_NAME --region $REGION --project $PROJECT_ID" -ForegroundColor White
Write-Host "List services: gcloud run services list --project $PROJECT_ID" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
