#!/bin/bash
# PSS Knowledge Assist - Quick Kubernetes Setup for Development
# This script sets up PostgreSQL in Kubernetes and shows connection details

echo "🚀 PSS Knowledge Assist - Kubernetes PostgreSQL Setup"
echo "=" * 60

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    echo "Please install kubectl first: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if Docker Desktop Kubernetes is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster is not accessible"
    echo "Please ensure Docker Desktop Kubernetes is enabled or you're connected to a cluster"
    exit 1
fi

echo "✅ Kubernetes cluster is accessible"

# Create namespace
echo "📁 Creating namespace..."
kubectl create namespace pss-knowledge-assist --dry-run=client -o yaml | kubectl apply -f -

# Deploy PostgreSQL
echo "🗄️ Deploying PostgreSQL..."
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres-deployment -n pss-knowledge-assist

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready!"
else
    echo "⚠️ PostgreSQL deployment might still be starting..."
fi

# Get PostgreSQL pod info
echo "📊 PostgreSQL Pod Status:"
kubectl get pods -n pss-knowledge-assist -l app=postgres

# Setup port forwarding
echo ""
echo "🔗 Setting up port forwarding..."
echo "Run this command in a separate terminal:"
echo "kubectl port-forward service/postgres-service 5432:5432 -n pss-knowledge-assist"
echo ""
echo "Then update your .env file with these settings:"
echo "DB_HOST=localhost"
echo "DB_PORT=5432"
echo "DB_USER=postgres"
echo "DB_PASSWORD=your-secure-password-here"
echo ""
echo "🔧 To connect to PostgreSQL:"
echo "1. Run port forwarding: kubectl port-forward service/postgres-service 5432:5432 -n pss-knowledge-assist"
echo "2. Update .env file with DB_HOST=localhost"
echo "3. Run database setup: python scripts/setup_pss_database.py"
echo "4. Start the application: python -m uvicorn app.main:app --host 0.0.0.0 --port 8080"
echo ""
echo "🌐 Application will be available at: http://localhost:8080"
