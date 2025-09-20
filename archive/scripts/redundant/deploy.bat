@echo off
REM PSS Knowledge Assist Deployment Script for Windows
REM This script deploys the PSS Knowledge Assist application to Kubernetes

echo  Starting PSS Knowledge Assist Kubernetes Deployment

REM Check if kubectl is available
kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo  kubectl is not installed or not in PATH
    exit /b 1
)

REM Check if docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo  docker is not installed or not in PATH
    exit /b 1
)

REM Set variables
set NAMESPACE=pss-knowledge-assist
set APP_NAME=pss-knowledge-assist
if "%1"=="" (
    set VERSION=latest
) else (
    set VERSION=%1
)

echo  Deployment Configuration:
echo    Namespace: %NAMESPACE%
echo    App Name: %APP_NAME%
echo    Version: %VERSION%

REM Build Docker image
echo � Building Docker image...
docker build -t %APP_NAME%:%VERSION% .

REM Tag for registry (update with your registry)
echo �️  Tagging image for registry...
REM docker tag %APP_NAME%:%VERSION% your-registry.com/%APP_NAME%:%VERSION%
REM docker push your-registry.com/%APP_NAME%:%VERSION%

REM Create namespace if it doesn't exist
echo � Creating namespace...
kubectl create namespace %NAMESPACE% --dry-run=client -o yaml | kubectl apply -f -

REM Deploy PostgreSQL
echo �️  Deploying PostgreSQL...
kubectl apply -f k8s/postgres-deployment.yaml

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
kubectl wait --for=condition=available --timeout=300s deployment/postgres-deployment -n %NAMESPACE%

REM Deploy the application
echo  Deploying PSS Knowledge Assist application...
kubectl apply -f k8s/app-deployment.yaml

REM Wait for application to be ready
echo ⏳ Waiting for application to be ready...
kubectl wait --for=condition=available --timeout=300s deployment/%APP_NAME%-deployment -n %NAMESPACE%

REM Run database migrations
echo  Running database migrations...
kubectl exec -n %NAMESPACE% deployment/%APP_NAME%-deployment -- python -m alembic upgrade head

echo  Deployment completed successfully!

REM Get service information
echo  Service Information:
kubectl get services -n %NAMESPACE%

echo  To check the status:
echo    kubectl get pods -n %NAMESPACE%
echo    kubectl logs -f deployment/%APP_NAME%-deployment -n %NAMESPACE%

echo  To access the application:
echo    kubectl port-forward service/%APP_NAME%-service 8080:80 -n %NAMESPACE%
echo    Then visit: http://localhost:8080
