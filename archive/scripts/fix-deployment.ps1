# Fix Google Cloud Run Deployment Issues
# Service Account and API Setup

Write-Host " Fixing Google Cloud Run Deployment Issues" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "pbm-dev-careassist-genai-poc"
$SERVICE_NAME = "pss-knowledge-assist"
$REGION = "us-central1"

Write-Host " Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host ""

# Step 1: Enable all required APIs
Write-Host " Enabling all required APIs..." -ForegroundColor Yellow
$apis = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com", 
    "artifactregistry.googleapis.com",
    "containerregistry.googleapis.com",
    "iam.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "   Enabling $api..." -ForegroundColor White
    gcloud services enable $api --project=$PROJECT_ID --quiet
}

if ($LASTEXITCODE -eq 0) {
    Write-Host " All APIs enabled successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️ Some APIs may have failed to enable" -ForegroundColor Yellow
}
Write-Host ""

# Step 2: Fix Cloud Build service account
Write-Host " Fixing Cloud Build service account..." -ForegroundColor Yellow
$projectNumber = gcloud projects describe $PROJECT_ID --format="value(projectNumber)" 2>$null
$serviceAccount = "$projectNumber-compute@developer.gserviceaccount.com"

Write-Host "   Service Account: $serviceAccount" -ForegroundColor White

# Enable the service account
Write-Host "   Enabling service account..." -ForegroundColor White
gcloud iam service-accounts enable $serviceAccount --project=$PROJECT_ID 2>$null

# Add required roles
Write-Host "   Adding Cloud Build roles..." -ForegroundColor White
$roles = @(
    "roles/cloudbuild.builds.builder",
    "roles/storage.admin",
    "roles/artifactregistry.admin"
)

foreach ($role in $roles) {
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$serviceAccount" `
        --role=$role --quiet 2>$null
}

Write-Host " Service account configuration complete" -ForegroundColor Green
Write-Host ""

# Step 3: Try deployment again
Write-Host " Attempting deployment again..." -ForegroundColor Cyan
Write-Host "   This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

gcloud run deploy $SERVICE_NAME `
    --source . `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --memory 1Gi `
    --cpu 1 `
    --max-instances 10 `
    --set-env-vars="LOG_LEVEL=INFO,ENVIRONMENT=production,DATABASE_URL=sqlite:///app.db,SECRET_KEY=prod-secret-pss-2025" `
    --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host " Deployment successful!" -ForegroundColor Green
    Write-Host ""
    
    # Get service URL
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project $PROJECT_ID 2>$null
    
    if (-not [string]::IsNullOrEmpty($serviceUrl)) {
        Write-Host " Service URL: $serviceUrl" -ForegroundColor Green
        Write-Host ""
        Write-Host " PSS Knowledge Assist is live!" -ForegroundColor Green
        Write-Host ""
        Write-Host "� PUBLIC URL: $serviceUrl" -ForegroundColor Cyan
        Write-Host "� Test Login: admin@pss-knowledge-assist.com / password123" -ForegroundColor White
        Write-Host ""
        
        $openBrowser = Read-Host "Open application in browser? (Y/N)"
        if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
            Start-Process $serviceUrl
        }
    }
} else {
    Write-Host ""
    Write-Host " Deployment still failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Try manual Docker build approach" -ForegroundColor Yellow
    Write-Host "Run: .\deploy-docker-manual.ps1" -ForegroundColor Cyan
}

Write-Host ""
Read-Host "Press Enter to exit"
