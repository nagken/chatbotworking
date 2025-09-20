# Cloud Deployment Setup for PSS Knowledge Assist

## 🌐 Cloud Deployment Options

### 1. **Google Cloud Run** (Recommended)
- **Serverless** - Pay only when used
- **Auto-scaling** - Scales to zero when not used
- **HTTPS by default** - Secure SSL/TLS termination
- **Global** - Available worldwide
- **Cost-effective** - Usually free tier eligible

### 2. **Other Cloud Options**
- **AWS ECS Fargate** - Similar serverless container service
- **Azure Container Instances** - Microsoft's container service
- **DigitalOcean App Platform** - Simple deployment platform
- **Railway** - Developer-friendly platform
- **Render** - Easy container deployment

## 🚀 Google Cloud Run Deployment

### **Prerequisites**
1. **Google Cloud Account** (free tier available)
2. **GitHub Repository** with your code
3. **Docker image** (we already have this)

### **Setup Steps**

#### **1. Enable Google Cloud Services**
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### **2. Build and Deploy Manually**
```bash
# Build and submit to Google Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pss-knowledge-assist

# Deploy to Cloud Run
gcloud run deploy pss-knowledge-assist \
  --image gcr.io/YOUR_PROJECT_ID/pss-knowledge-assist \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

#### **3. GitHub Actions Automated Deployment**
See `.github/workflows/deploy-cloud-run.yml` (created below)

### **Environment Variables for Cloud Run**
```yaml
# Set in Cloud Run service
LOG_LEVEL: INFO
ENVIRONMENT: production
DEBUG_MODE: false
SECRET_KEY: your-production-secret-key
```

### **Custom Domain (Optional)**
```bash
# Map custom domain
gcloud run domain-mappings create \
  --service pss-knowledge-assist \
  --domain your-domain.com \
  --region us-central1
```

## 🔄 GitHub Actions CI/CD

The GitHub Actions workflow will:
1. **Build** Docker image on every push
2. **Test** the deployment
3. **Deploy** to Google Cloud Run
4. **Notify** on success/failure

## 💰 Estimated Costs

### **Google Cloud Run (Free Tier)**
- **2 million requests** per month - FREE
- **360,000 GB-seconds** per month - FREE
- **180,000 vCPU-seconds** per month - FREE

**For PSS Knowledge Assist**: Likely to stay within free tier for testing/demo purposes.

### **GitHub Actions**
- **2,000 minutes** per month - FREE for public repos
- **500 MB storage** - FREE

## 🌍 Public Access URLs

Once deployed, your application will be available at:
- **https://pss-knowledge-assist-[random-hash]-uc.a.run.app**
- **Custom domain** (if configured): https://your-domain.com

## 🛡️ Security Considerations

### **Production Security**
- ✅ HTTPS by default (Cloud Run)
- ✅ Isolated container environment
- ✅ No database credentials needed (uses mock data)
- ✅ Non-root user in container
- ⚠️ Change default SECRET_KEY in production

### **Access Control**
- **Public** - Anyone can access (current setup)
- **IAM** - Restrict to specific Google accounts
- **Custom Auth** - Add your own authentication layer

## 📊 Monitoring & Logs

### **Cloud Run Console**
- View request metrics
- Check error rates
- Monitor response times
- View container logs

### **Logs**
```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision" --limit 100

# Follow logs in real-time
gcloud logs tail "resource.type=cloud_run_revision"
```

## 🔧 Troubleshooting

### **Common Issues**
1. **Build fails** - Check Dockerfile and dependencies
2. **Service won't start** - Check logs and health endpoints
3. **403 errors** - Verify IAM permissions
4. **Timeout errors** - Increase memory/CPU allocation

### **Debug Commands**
```bash
# Check service status
gcloud run services describe pss-knowledge-assist --region us-central1

# View recent deployments
gcloud run revisions list --service pss-knowledge-assist --region us-central1

# Check logs
gcloud logs read "resource.type=cloud_run_revision" --limit 50
```

## 🎯 Quick Start Commands

### **Deploy from Local Machine**
```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy in one command
gcloud run deploy pss-knowledge-assist \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

This will give you a public URL that anyone can use to test your PSS Knowledge Assist application!
