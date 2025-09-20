#!/bin/bash

# PSS Knowledge Assist Deployment Script
# This script deploys the PSS Knowledge Assist application to Kubernetes

set -e

echo "🚀 Starting PSS Knowledge Assist Kubernetes Deployment"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if docker is available for building
if ! command -v docker &> /dev/null; then
    echo "❌ docker is not installed or not in PATH"
    exit 1
fi

# Set variables
NAMESPACE="pss-knowledge-assist"
APP_NAME="pss-knowledge-assist"
VERSION=${1:-latest}

echo "📋 Deployment Configuration:"
echo "   Namespace: $NAMESPACE"
echo "   App Name: $APP_NAME"
echo "   Version: $VERSION"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t $APP_NAME:$VERSION .

# Tag for registry (update with your registry)
echo "🏷️  Tagging image for registry..."
# docker tag $APP_NAME:$VERSION your-registry.com/$APP_NAME:$VERSION
# docker push your-registry.com/$APP_NAME:$VERSION

# Create namespace if it doesn't exist
echo "📁 Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy PostgreSQL
echo "🗄️  Deploying PostgreSQL..."
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres-deployment -n $NAMESPACE

# Deploy the application
echo "🚀 Deploying PSS Knowledge Assist application..."
kubectl apply -f k8s/app-deployment.yaml

# Wait for application to be ready
echo "⏳ Waiting for application to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/$APP_NAME-deployment -n $NAMESPACE

# Run database migrations
echo "🔄 Running database migrations..."
kubectl exec -n $NAMESPACE deployment/$APP_NAME-deployment -- python -m alembic upgrade head

echo "✅ Deployment completed successfully!"

# Get service information
echo "📊 Service Information:"
kubectl get services -n $NAMESPACE

echo "🔍 To check the status:"
echo "   kubectl get pods -n $NAMESPACE"
echo "   kubectl logs -f deployment/$APP_NAME-deployment -n $NAMESPACE"

echo "🌐 To access the application:"
echo "   kubectl port-forward service/$APP_NAME-service 8080:80 -n $NAMESPACE"
echo "   Then visit: http://localhost:8080"
