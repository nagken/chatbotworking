# Workaround for CMEK Organizational Policy Issue
# Deploy using Container Registry instead of Artifact Registry

Write-Host "CMEK Policy Workaround - Using Container Registry" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "pbm-dev-careassist-genai-poc"
$SERVICE_NAME = "pss-knowledge-assist"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Using Container Registry instead of Artifact Registry" -ForegroundColor Yellow
Write-Host ""

# Step 1: Enable Container Registry API
Write-Host "Enabling Container Registry API..." -ForegroundColor Yellow
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID --quiet

Write-Host "Container Registry API enabled" -ForegroundColor Green
Write-Host ""

# Step 2: Configure Docker for Google Cloud
Write-Host "Configuring Docker authentication..." -ForegroundColor Yellow
gcloud auth configure-docker --quiet

Write-Host "Docker configured" -ForegroundColor Green
Write-Host ""

# Step 3: Build image locally
Write-Host "Building Docker image locally..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor White
Write-Host ""

docker build -t $IMAGE_NAME .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure Docker Desktop is running" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Docker image built successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Push to Container Registry
Write-Host "Pushing image to Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to push image" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Image pushed successfully" -ForegroundColor Green
Write-Host ""

# Step 5: Deploy to Cloud Run using the image
Write-Host "Deploying to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME --region $REGION --platform managed --allow-unauthenticated --port 8080 --memory 1Gi --cpu 1 --max-instances 10 --set-env-vars="LOG_LEVEL=INFO,ENVIRONMENT=production,DATABASE_URL=sqlite:///app.db,SECRET_KEY=prod-secret-pss-2025" --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Deployment successful!" -ForegroundColor Green
    Write-Host ""
    
    # Get service URL
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project $PROJECT_ID
    
    if ($serviceUrl) {
        Write-Host "Service URL: $serviceUrl" -ForegroundColor Green
        Write-Host ""
        Write-Host "PSS Knowledge Assist is live!" -ForegroundColor Green
        Write-Host ""
        Write-Host "PUBLIC URL: $serviceUrl" -ForegroundColor Cyan
        Write-Host "Test Login: admin@pss-knowledge-assist.com / password123" -ForegroundColor White
        Write-Host ""
        Write-Host "Share this URL for external testing!" -ForegroundColor Cyan
        Write-Host ""
        
        $openBrowser = Read-Host "Open application in browser? (Y/N)"
        if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
            Start-Process $serviceUrl
        }
    }
} else {
    Write-Host ""
    Write-Host "Deployment failed" -ForegroundColor Red
    Write-Host "Check the error messages above for details" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
