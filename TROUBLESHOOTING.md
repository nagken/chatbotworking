# 🔧 Deployment Troubleshooting - PSS Knowledge Assist

## 🚨 SSL Certificate Issues (Docker Build Failed)

You're experiencing SSL certificate verification errors when Docker tries to download Python packages. This is common in corporate environments.

## 🚀 **IMMEDIATE SOLUTIONS** (Pick One)

### **Option 1: Simple Local Python** ⚡ (Recommended)
```bat
# Run this if you have Python installed:
deploy-simple.bat
```

### **Option 2: Manual Python Setup** 🐍
```bat
# Install packages manually:
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org fastapi uvicorn sqlalchemy alembic bcrypt python-jose python-multipart requests

# Run the app:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **Option 3: Use Existing run_server.bat** 📁
```bat
# If you already have Python packages installed:
./run_server.bat
```

### **Option 4: Cloud Deployment** ☁️ (Skip local issues entirely)
Use Railway, Render, or Google Cloud Run (see QUICK_DEPLOYMENT_GUIDE.md)

## 🔍 **ROOT CAUSE ANALYSIS**

The error occurs because:
1. **Corporate firewall/proxy** blocks SSL connections to PyPI
2. **Docker Desktop network settings** interfere with SSL
3. **VPN** causes certificate validation issues
4. **Windows certificate store** not accessible to Docker

## 🛠️ **PERMANENT FIXES**

### **Fix 1: Docker Network Settings**
1. Open Docker Desktop
2. Settings → Resources → Network
3. Try different DNS servers:
   - `8.8.8.8, 8.8.4.4` (Google)
   - `1.1.1.1, 1.0.0.1` (Cloudflare)

### **Fix 2: Corporate Network**
1. **Temporarily disable VPN**
2. **Use mobile hotspot** for Docker build
3. **Contact IT** about PyPI access
4. **Use corporate proxy settings** in Docker

### **Fix 3: Windows Certificate Fix**
```bat
# Update Windows certificates
certlm.msc
# Import corporate certificates if needed
```

### **Fix 4: Docker Proxy Configuration**
Create `~/.docker/config.json`:
```json
{
  "proxies": {
    "default": {
      "httpProxy": "http://your-proxy:port",
      "httpsProxy": "http://your-proxy:port"
    }
  }
}
```

## 🎯 **RECOMMENDED APPROACH**

For immediate testing:
1. **Try `deploy-simple.bat`** (uses local Python)
2. **If that fails, use Railway/Render** for cloud deployment
3. **Fix Docker later** for local development

## 📋 **Quick Test Commands**

```bat
# Test Python availability
python --version

# Test package installation
pip install --trusted-host pypi.org fastapi

# Test direct app run
python -m uvicorn app.main:app --port 8000

# Test Docker without build
docker run hello-world
```

## 🌐 **Cloud Alternatives (No Local Issues)**

### **Railway (2 minutes)**
1. Go to https://railway.app
2. Sign up with GitHub
3. Deploy from repository
4. Get instant public URL

### **Render (5 minutes)**
1. Go to https://render.com
2. Connect GitHub repo
3. Select "Web Service"
4. Choose "Docker" runtime
5. Deploy automatically

### **Google Cloud Run (10 minutes)**
```bat
# If gcloud CLI is installed:
./deploy-cloud-run.bat
```

## 💡 **Next Steps**

1. **Try `deploy-simple.bat` first**
2. **If it works**: You have a running app at http://localhost:8000
3. **If it doesn't**: Use cloud deployment (Railway recommended)
4. **For sharing**: Cloud deployment gives you a public URL
5. **For local development**: Fix Docker SSL issues later

## 🎉 **Success Indicators**

When working correctly, you should see:
- ✅ Login page at http://localhost:8000 (or cloud URL)
- ✅ Chat interface after login
- ✅ Bot responses to your messages
- ✅ Thumbs up/down feedback buttons
- ✅ Conversation history in sidebar

## 🆘 **Still Stuck?**

If all options fail:
1. **Share error messages** - I can provide specific fixes
2. **Try different network** (mobile hotspot)
3. **Use GitHub Actions** for automatic cloud deployment
4. **Contact IT support** about PyPI/Docker access
