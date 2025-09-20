# PSS Knowledge Assist Server Startup Script
Write-Host "========================================" -ForegroundColor Green
Write-Host "PSS Knowledge Assist - Server Startup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Set-Location "c:\cvssep9"
Write-Host "Starting server on port 8080..." -ForegroundColor Yellow
Write-Host ""
Write-Host "The application will be available at:" -ForegroundColor Cyan
Write-Host "  - http://localhost:8080" -ForegroundColor Cyan
Write-Host "  - http://127.0.0.1:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
