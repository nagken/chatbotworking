# Create Local Docker Image for Railway Import

Write-Host "Creating Local Docker Image for Railway Import" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

$IMAGE_NAME = "pss-knowledge-assist"
$TAR_FILE = "pss-knowledge-assist-docker.tar"

Write-Host "This will create a Docker image file you can import to Railway" -ForegroundColor Yellow
Write-Host ""

# Step 1: Cancel any running Docker build
Write-Host "Step 1: Stop any running Docker processes..." -ForegroundColor Yellow
docker system prune -f 2>$null
Write-Host "Docker cleaned up" -ForegroundColor Green
Write-Host ""

# Step 2: Check if we can use a faster base image or cached layers
Write-Host "Step 2: Checking for cached Python images..." -ForegroundColor Yellow
$pythonImages = docker images python --format "table {{.Repository}}:{{.Tag}}"
if ($pythonImages) {
    Write-Host "Found cached Python images:" -ForegroundColor Green
    Write-Host $pythonImages -ForegroundColor White
} else {
    Write-Host "No cached Python images found" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Create optimized Dockerfile for local build
Write-Host "Step 3: Creating optimized Dockerfile..." -ForegroundColor Yellow

$optimizedDockerfile = @"
# Optimized Dockerfile for local build
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
"@

$optimizedDockerfile | Out-File -FilePath "Dockerfile.local" -Encoding UTF8
Write-Host "Optimized Dockerfile created: Dockerfile.local" -ForegroundColor Green
Write-Host ""

# Step 4: Build Docker image locally
Write-Host "Step 4: Building Docker image locally..." -ForegroundColor Yellow
Write-Host "This may take 10-15 minutes..." -ForegroundColor White
Write-Host ""

docker build -f Dockerfile.local -t $IMAGE_NAME .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting options:" -ForegroundColor Yellow
    Write-Host "1. Check if Docker Desktop is running" -ForegroundColor White
    Write-Host "2. Try building with no cache: docker build --no-cache -f Dockerfile.local -t $IMAGE_NAME ." -ForegroundColor White
    Write-Host "3. Try different network (mobile hotspot)" -ForegroundColor White
    Write-Host "4. Use Railway direct GitHub deployment instead" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Docker image built successfully!" -ForegroundColor Green
Write-Host ""

# Step 5: Save Docker image to tar file
Write-Host "Step 5: Saving Docker image to file..." -ForegroundColor Yellow
docker save -o $TAR_FILE $IMAGE_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host "Docker image saved to: $TAR_FILE" -ForegroundColor Green
    
    # Get file size
    $fileSize = (Get-Item $TAR_FILE).Length / 1MB
    Write-Host "File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor White
} else {
    Write-Host "Failed to save Docker image" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "SUCCESS! Docker image ready for Railway import" -ForegroundColor Green
Write-Host ""

# Step 6: Instructions for Railway
Write-Host "Next Steps for Railway Deployment:" -ForegroundColor Cyan
Write-Host ""
Write-Host "OPTION A: Upload Docker Image to Railway" -ForegroundColor Yellow
Write-Host "1. Go to: https://railway.app" -ForegroundColor White
Write-Host "2. Sign up/login with GitHub" -ForegroundColor White
Write-Host "3. Create New Project" -ForegroundColor White
Write-Host "4. Deploy Docker Image" -ForegroundColor White
Write-Host "5. Upload file: $TAR_FILE" -ForegroundColor Cyan
Write-Host ""

Write-Host "OPTION B: Push to Docker Hub (if you have account)" -ForegroundColor Yellow
Write-Host "docker tag $IMAGE_NAME yourusername/pss-knowledge-assist" -ForegroundColor Cyan
Write-Host "docker push yourusername/pss-knowledge-assist" -ForegroundColor Cyan
Write-Host "Then deploy from Docker Hub on Railway" -ForegroundColor White
Write-Host ""

Write-Host "OPTION C: GitHub + Railway (Easiest)" -ForegroundColor Yellow
Write-Host "1. Push your code to GitHub" -ForegroundColor White
Write-Host "2. Go to Railway.app" -ForegroundColor White
Write-Host "3. Deploy from GitHub repository" -ForegroundColor White
Write-Host "4. Railway builds automatically" -ForegroundColor White
Write-Host ""

# Step 7: Test locally first
Write-Host "Test locally first:" -ForegroundColor Green
Write-Host "docker run -p 8080:8080 $IMAGE_NAME" -ForegroundColor Cyan
Write-Host "Then visit: http://localhost:8080" -ForegroundColor White
Write-Host ""

$choice = Read-Host "What would you like to do? (1=Test locally, 2=Open Railway, 3=Show commands, Enter=Continue)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Testing Docker image locally..." -ForegroundColor Green
        Write-Host "Visit http://localhost:8080 to test" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        docker run -p 8080:8080 $IMAGE_NAME
    }
    "2" {
        Write-Host ""
        Write-Host "Opening Railway.app..." -ForegroundColor Green
        Start-Process "https://railway.app"
        Write-Host "Upload the file: $TAR_FILE" -ForegroundColor Cyan
    }
    "3" {
        Write-Host ""
        Write-Host "Commands Summary:" -ForegroundColor Yellow
        Write-Host "Test locally: docker run -p 8080:8080 $IMAGE_NAME" -ForegroundColor Cyan
        Write-Host "Upload to Railway: Use file $TAR_FILE" -ForegroundColor Cyan
        Write-Host "Deploy from GitHub: Push code and use Railway GitHub integration" -ForegroundColor Cyan
    }
    default {
        Write-Host ""
        Write-Host "Docker image ready! File: $TAR_FILE" -ForegroundColor Green
        Write-Host "Upload to Railway.app for instant deployment" -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "Press Enter to exit"
