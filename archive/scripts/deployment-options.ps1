# Alternative Cloud Deployment Options
# When Google Cloud Run has organizational policy restrictions

Write-Host "Alternative Cloud Deployment Options" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Your Google Cloud project has CMEK (Customer-Managed Encryption Keys) restrictions." -ForegroundColor Yellow
Write-Host "This is common in enterprise/corporate environments." -ForegroundColor Yellow
Write-Host ""

Write-Host "Here are your deployment options:" -ForegroundColor White
Write-Host ""

Write-Host "OPTION 1: Container Registry Workaround (Recommended)" -ForegroundColor Green
Write-Host "Run: .\deploy-container-registry.ps1" -ForegroundColor Cyan
Write-Host "- Uses Google Container Registry instead of Artifact Registry" -ForegroundColor White
Write-Host "- Bypasses the CMEK requirement" -ForegroundColor White
Write-Host "- Still deploys to Google Cloud Run" -ForegroundColor White
Write-Host ""

Write-Host "OPTION 2: Railway (Fastest Alternative)" -ForegroundColor Green
Write-Host "1. Go to: https://railway.app" -ForegroundColor Cyan
Write-Host "2. Sign up with GitHub" -ForegroundColor White
Write-Host "3. Deploy from repository" -ForegroundColor White
Write-Host "4. Get instant public URL" -ForegroundColor White
Write-Host "- No organizational policies" -ForegroundColor White
Write-Host "- 2-minute deployment" -ForegroundColor White
Write-Host "- Free tier available" -ForegroundColor White
Write-Host ""

Write-Host "OPTION 3: Render" -ForegroundColor Green
Write-Host "1. Go to: https://render.com" -ForegroundColor Cyan
Write-Host "2. New > Web Service" -ForegroundColor White
Write-Host "3. Connect GitHub repository" -ForegroundColor White
Write-Host "4. Select Docker runtime" -ForegroundColor White
Write-Host "- Free tier available" -ForegroundColor White
Write-Host "- Automatic SSL" -ForegroundColor White
Write-Host ""

Write-Host "OPTION 4: DigitalOcean App Platform" -ForegroundColor Green
Write-Host "1. Go to: https://cloud.digitalocean.com/apps" -ForegroundColor Cyan
Write-Host "2. Create App > GitHub" -ForegroundColor White
Write-Host "3. Select repository" -ForegroundColor White
Write-Host "4. Choose Docker deployment" -ForegroundColor White
Write-Host "- $5/month (no free tier)" -ForegroundColor White
Write-Host "- Very reliable" -ForegroundColor White
Write-Host ""

Write-Host "RECOMMENDED ACTION:" -ForegroundColor Yellow
Write-Host "1. Try Container Registry workaround first: .\deploy-container-registry.ps1" -ForegroundColor Cyan
Write-Host "2. If that fails, use Railway for instant deployment" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Which option would you like to try? (1=Container Registry, 2=Railway, 3=Show manual commands)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting Container Registry deployment..." -ForegroundColor Green
        & ".\deploy-container-registry.ps1"
    }
    "2" {
        Write-Host ""
        Write-Host "Opening Railway.app..." -ForegroundColor Green
        Start-Process "https://railway.app"
        Write-Host "Sign up with GitHub and deploy from your repository" -ForegroundColor Yellow
    }
    "3" {
        Write-Host ""
        Write-Host "Manual Container Registry Commands:" -ForegroundColor Yellow
        Write-Host "gcloud services enable containerregistry.googleapis.com --project pbm-dev-careassist-genai-poc" -ForegroundColor Cyan
        Write-Host "gcloud auth configure-docker" -ForegroundColor Cyan
        Write-Host "docker build -t gcr.io/pbm-dev-careassist-genai-poc/pss-knowledge-assist ." -ForegroundColor Cyan
        Write-Host "docker push gcr.io/pbm-dev-careassist-genai-poc/pss-knowledge-assist" -ForegroundColor Cyan
        Write-Host "gcloud run deploy pss-knowledge-assist --image gcr.io/pbm-dev-careassist-genai-poc/pss-knowledge-assist --region us-central1 --allow-unauthenticated --port 8080 --memory 1Gi --project pbm-dev-careassist-genai-poc" -ForegroundColor Cyan
    }
    default {
        Write-Host "Run .\deploy-container-registry.ps1 to try the Container Registry workaround" -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "Press Enter to exit"
