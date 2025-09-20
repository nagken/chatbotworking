# PSS Knowledge Assist - Docker Quick Start Guide

## 🐳 Docker Deployment

The PSS Knowledge Assist application is fully containerized and ready for Docker deployment. This ensures a consistent, isolated environment that works the same everywhere.

## 📋 Prerequisites

- **Docker** installed and running
- **Git** (to clone/update the repository)

## 🚀 Quick Start Commands

### **1. Build and Run (One Command)**
```bash
# Build and start the application
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### **2. Manual Docker Commands**
```bash
# Build the image
docker build -t pss-knowledge-assist .

# Run the container
docker run -p 8080:8080 --name pss-app pss-knowledge-assist

# Run in background
docker run -d -p 8080:8080 --name pss-app pss-knowledge-assist
```

### **3. Access the Application**
Once running, access the application at:
- **http://localhost:8080**
- **http://127.0.0.1:8080**

## 🛠️ Management Commands

### **Stop and Remove**
```bash
# Stop the container
docker stop pss-app

# Remove the container
docker rm pss-app

# Remove the image
docker rmi pss-knowledge-assist
```

### **View Logs**
```bash
# View container logs
docker logs pss-app

# Follow logs in real-time
docker logs -f pss-app
```

### **Restart**
```bash
# Restart the container
docker restart pss-app
```

## 📦 Docker Compose Setup

The application includes a `docker-compose.yml` file for easy orchestration:

```yaml
version: '3.8'
services:
  pss-app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=INFO
      - ENVIRONMENT=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔧 Environment Configuration

### **Environment Variables**
```bash
# Database (optional - app works with mock data)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pss_db

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG_MODE=false

# Authentication
SECRET_KEY=your-secret-key-here
```

### **Production Setup**
```bash
# Create production environment file
echo "LOG_LEVEL=INFO" > .env
echo "ENVIRONMENT=production" >> .env
echo "DEBUG_MODE=false" >> .env

# Run with environment file
docker-compose --env-file .env up -d
```

## 🏥 Health Monitoring

### **Health Check Endpoint**
```bash
# Check application health
curl http://localhost:8080/api/health

# Quick system test
curl http://localhost:8080/quick-test
```

### **Container Health**
```bash
# Check container health status
docker ps

# Inspect health check results
docker inspect pss-app | grep -A 5 Health
```

## 🔄 Updates and Maintenance

### **Update Application**
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### **Backup and Restore**
```bash
# Export container as image
docker commit pss-app pss-knowledge-assist:backup

# Save image to file
docker save pss-knowledge-assist:backup > pss-backup.tar

# Load image from file
docker load < pss-backup.tar
```

## 🐛 Troubleshooting

### **Common Issues**

**Port already in use:**
```bash
# Find process using port 8080
netstat -ano | findstr 8080

# Kill process or use different port
docker run -p 8081:8080 --name pss-app pss-knowledge-assist
```

**Container won't start:**
```bash
# Check logs for errors
docker logs pss-app

# Run interactively for debugging
docker run -it --rm pss-knowledge-assist bash
```

**Application not responding:**
```bash
# Check if container is running
docker ps -a

# Restart container
docker restart pss-app

# Check health
curl http://localhost:8080/api/health
```

## 🌐 Production Deployment

### **Docker Hub (Optional)**
```bash
# Tag for Docker Hub
docker tag pss-knowledge-assist username/pss-knowledge-assist:latest

# Push to Docker Hub
docker push username/pss-knowledge-assist:latest

# Pull and run from Docker Hub
docker run -p 8080:8080 username/pss-knowledge-assist:latest
```

### **Cloud Deployment**
- **AWS ECS**: Use the provided Dockerfile
- **Google Cloud Run**: Compatible with container deployment
- **Azure Container Instances**: Ready for deployment
- **Kubernetes**: Use the included k8s manifests

## ✅ Advantages of Docker Deployment

1. **Consistency**: Same environment everywhere
2. **Isolation**: No conflicts with host system
3. **Portability**: Run on any Docker-enabled system
4. **Scalability**: Easy to scale with orchestration
5. **Mock Fallback**: Works without external dependencies
6. **Health Monitoring**: Built-in health checks
7. **Security**: Non-root user, minimal attack surface

## 🎯 Quick Commands Summary

```bash
# One-line deployment
docker run -d -p 8080:8080 --name pss-app $(docker build -q .)

# Access application
open http://localhost:8080

# View logs
docker logs -f pss-app

# Stop and cleanup
docker stop pss-app && docker rm pss-app
```

The application includes robust mock data fallback, so it will work reliably in any Docker environment, even without database connectivity!
