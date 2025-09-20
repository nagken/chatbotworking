# Fix Google Cloud Run Deployment - Clean Version
Write-Host "Fixing Google Cloud Run Deployment Issues" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "pbm-dev-careassist-genai-poc"
$SERVICE_NAME = "pss-knowledge-assist"
$REGION = "us-central1"

Write-Host "Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host ""

# Step 1: Enable APIs
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com iam.googleapis.com --project=$PROJECT_ID --quiet

Write-Host "APIs enabled successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Fix service account
Write-Host "Fixing Cloud Build service account..." -ForegroundColor Yellow
$serviceAccount = "877124114577-compute@developer.gserviceaccount.com"

Write-Host "Enabling service account: $serviceAccount" -ForegroundColor White
gcloud iam service-accounts enable $serviceAccount --project=$PROJECT_ID

Write-Host "Adding required roles..." -ForegroundColor White
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$serviceAccount" --role="roles/cloudbuild.builds.builder" --quiet
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$serviceAccount" --role="roles/storage.admin" --quiet

Write-Host "Service account fixed successfully" -ForegroundColor Green
Write-Host ""

# Step 3: Try deployment
Write-Host "Attempting deployment..." -ForegroundColor Cyan
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

gcloud run deploy $SERVICE_NAME --source . --region $REGION --platform managed --allow-unauthenticated --port 8080 --memory 1Gi --cpu 1 --max-instances 10 --set-env-vars="LOG_LEVEL=INFO,ENVIRONMENT=production,DATABASE_URL=sqlite:///app.db,SECRET_KEY=prod-secret-pss-2025" --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Deployment successful!" -ForegroundColor Green
    Write-Host ""
    
    # Get service URL
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project $PROJECT_ID
    
    Write-Host "Service URL: $serviceUrl" -ForegroundColor Green
    Write-Host ""
    Write-Host "PSS Knowledge Assist is live!" -ForegroundColor Green
    Write-Host ""
    Write-Host "PUBLIC URL: $serviceUrl" -ForegroundColor Cyan
    Write-Host "Test Login: admin@pss-knowledge-assist.com / password123" -ForegroundColor White
    Write-Host ""
    
    $openBrowser = Read-Host "Open application in browser? (Y/N)"
    if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
        Start-Process $serviceUrl
    }
} else {
    Write-Host ""
    Write-Host "Deployment failed" -ForegroundColor Red
    Write-Host "Try manual Docker approach: .\deploy-docker-simple.ps1" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
