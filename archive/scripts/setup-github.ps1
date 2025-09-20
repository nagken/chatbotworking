# Git Setup and GitHub Push - PSS Knowledge Assist

Write-Host "Setting up Git and pushing to GitHub" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check current status
Write-Host "Current Git status:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "Setting up .gitignore..." -ForegroundColor Yellow

# Create or update .gitignore
$gitignoreContent = @"
# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database
*.db
*.sqlite
*.sqlite3
app.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
*.tar
docker-compose.override.yml

# Logs
*.log
logs/

# Temporary files
temp/
tmp/

# Node modules (if any)
node_modules/

# Backup files
*.bak
*.backup
"@

$gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
Write-Host ".gitignore created" -ForegroundColor Green
Write-Host ""

# Add all files except sensitive ones
Write-Host "Adding files to Git..." -ForegroundColor Yellow
git add .gitignore
git add README.md
git add requirements.txt
git add Dockerfile
git add Dockerfile.cloudrun
git add docker-compose.yml
git add alembic.ini
git add app/
git add static/
git add scripts/
git add k8s/
git add .github/
git add *.md
git add *.bat
git add *.ps1
git add *.py
git add *.sql

Write-Host "Files added to Git" -ForegroundColor Green
Write-Host ""

# Commit changes
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "Add PSS Knowledge Assist - Complete application with deployment configs"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Changes committed successfully" -ForegroundColor Green
} else {
    Write-Host "Commit may have failed or no changes to commit" -ForegroundColor Yellow
}

Write-Host ""

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your repository is now ready for deployment!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps for cloud deployment:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "OPTION 1: Railway (Recommended)" -ForegroundColor Green
    Write-Host "1. Go to: https://railway.app" -ForegroundColor White
    Write-Host "2. Sign up with GitHub" -ForegroundColor White
    Write-Host "3. Deploy from GitHub repo: chatbotsep1" -ForegroundColor White
    Write-Host "4. Get instant public URL" -ForegroundColor White
    Write-Host ""
    Write-Host "OPTION 2: Render" -ForegroundColor Green
    Write-Host "1. Go to: https://render.com" -ForegroundColor White
    Write-Host "2. New > Web Service" -ForegroundColor White
    Write-Host "3. Connect GitHub repo: chatbotsep1" -ForegroundColor White
    Write-Host "4. Runtime: Docker" -ForegroundColor White
    Write-Host ""
    
    $deploy = Read-Host "Open Railway for deployment? (Y/N)"
    if ($deploy -eq "Y" -or $deploy -eq "y") {
        Start-Process "https://railway.app"
        Write-Host ""
        Write-Host "Steps in Railway:" -ForegroundColor Yellow
        Write-Host "1. Click 'Deploy from GitHub repo'" -ForegroundColor White
        Write-Host "2. Select: nagken/chatbotsep1" -ForegroundColor White
        Write-Host "3. Railway will auto-detect Docker and deploy" -ForegroundColor White
        Write-Host "4. Get public URL in 2-3 minutes" -ForegroundColor White
    }
} else {
    Write-Host "Push failed. Common solutions:" -ForegroundColor Red
    Write-Host ""
    Write-Host "1. Check GitHub authentication:" -ForegroundColor Yellow
    Write-Host "   git config --global user.email 'your-email@example.com'" -ForegroundColor Cyan
    Write-Host "   git config --global user.name 'Your Name'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Try authentication:" -ForegroundColor Yellow
    Write-Host "   git remote set-url origin https://github.com/nagken/chatbotsep1.git" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Force push if needed:" -ForegroundColor Yellow
    Write-Host "   git push -f origin main" -ForegroundColor Cyan
}

Write-Host ""
Read-Host "Press Enter to exit"
