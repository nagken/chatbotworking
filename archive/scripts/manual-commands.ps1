# Manual Commands to Fix Google Cloud Run Deployment

Write-Host "Manual Fix Commands for Google Cloud Run" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "pbm-dev-careassist-genai-poc"
$SERVICE_ACCOUNT = "877124114577-compute@developer.gserviceaccount.com"

Write-Host "Run these commands one by one:" -ForegroundColor Yellow
Write-Host ""

Write-Host "1. Enable APIs:" -ForegroundColor White
Write-Host "gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project $PROJECT_ID" -ForegroundColor Cyan
Write-Host ""

Write-Host "2. Enable service account:" -ForegroundColor White  
Write-Host "gcloud iam service-accounts enable $SERVICE_ACCOUNT --project $PROJECT_ID" -ForegroundColor Cyan
Write-Host ""

Write-Host "3. Add required role:" -ForegroundColor White
Write-Host "gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SERVICE_ACCOUNT --role=roles/cloudbuild.builds.builder" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. Deploy application:" -ForegroundColor White
Write-Host "gcloud run deploy pss-knowledge-assist --source . --region us-central1 --allow-unauthenticated --port 8080 --memory 1Gi --project $PROJECT_ID" -ForegroundColor Cyan
Write-Host ""

Write-Host "Copy and paste each command above into PowerShell" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"
