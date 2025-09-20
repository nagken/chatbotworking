# PSS Knowledge Assist - Docker PowerShell Launcher
Write-Host "========================================" -ForegroundColor Green
Write-Host "PSS Knowledge Assist - Docker Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
try {
    $dockerVersion = docker version --format json | ConvertFrom-Json
    Write-Host " Docker is running (Client: $($dockerVersion.Client.Version))" -ForegroundColor Green
} catch {
    Write-Host " Docker is not running or not installed" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Function to check application health
function Test-ApplicationHealth {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/api/health" -TimeoutSec 3 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Function to wait for application to be ready
function Wait-ForApplication {
    Write-Host "⏳ Waiting for application to be ready..." -ForegroundColor Yellow
    $attempts = 0
    $maxAttempts = 30
    
    do {
        Start-Sleep -Seconds 2
        $attempts++
        if (Test-ApplicationHealth) {
            Write-Host " Application is ready!" -ForegroundColor Green
            return $true
        }
        Write-Host "   ... attempt $attempts/$maxAttempts" -ForegroundColor Gray
    } while ($attempts -lt $maxAttempts)
    
    Write-Host " Application failed to start within timeout" -ForegroundColor Red
    return $false
}

# Main deployment logic
Write-Host "� Starting PSS Knowledge Assist with Docker Compose..." -ForegroundColor Cyan
Write-Host ""

# Stop any existing containers
Write-Host "🧹 Cleaning up existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null
docker stop pss-app 2>$null
docker rm pss-app 2>$null

# Start with Docker Compose
Write-Host " Building and starting containers..." -ForegroundColor Yellow
docker-compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host " Docker Compose failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host " Containers started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "� Application URLs:" -ForegroundColor Cyan
Write-Host "    http://localhost:8080" -ForegroundColor White
Write-Host "    http://127.0.0.1:8080" -ForegroundColor White
Write-Host ""

# Wait for application to be ready
if (Wait-ForApplication) {
    Write-Host ""
    Write-Host " Container Status:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host " Management Commands:" -ForegroundColor Cyan
    Write-Host "   � View logs:  docker-compose logs -f" -ForegroundColor White
    Write-Host "   � Stop:       docker-compose down" -ForegroundColor White
    Write-Host "    Restart:    docker-compose restart" -ForegroundColor White
    Write-Host "    Health:     curl http://localhost:8080/api/health" -ForegroundColor White
    
    Write-Host ""
    Write-Host " Opening application in browser..." -ForegroundColor Green
    Start-Process "http://localhost:8080"
} else {
    Write-Host "� Check logs with: docker-compose logs" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to continue"
