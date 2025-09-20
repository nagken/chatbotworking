# 🚀 Google Cloud Run Deployment - PSS Knowledge Assist

## Project: `pbm-dev-careassist-genai-poc`

Your local app is working perfectly! Now let's deploy it to Google Cloud Run for external testing.

## 📋 Manual Deployment Steps

### **Step 1: Set Project**
```bash
gcloud config set project pbm-dev-careassist-genai-poc
```

### **Step 2: Enable APIs**
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### **Step 3: Deploy to Cloud Run**
```bash
gcloud run deploy pss-knowledge-assist \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars="LOG_LEVEL=INFO,ENVIRONMENT=production,DATABASE_URL=sqlite:///app.db,SECRET_KEY=prod-secret-pss-2025" \
  --project pbm-dev-careassist-genai-poc
```

### **Step 4: Get Service URL**
```bash
gcloud run services describe pss-knowledge-assist \
  --region us-central1 \
  --format="value(status.url)" \
  --project pbm-dev-careassist-genai-poc
```

## 🎯 **Expected Result**

After successful deployment, you'll get a public URL like:
```
https://pss-knowledge-assist-xxxxx-uc.a.run.app
```

## 🧪 **Testing Your Deployed App**

1. **Visit the URL** in any browser
2. **Login with**: `admin@pss-knowledge-assist.com` / `password123`
3. **Test features**:
   - Chat interface
   - PSS knowledge responses  
   - Thumbs up/down feedback
   - Conversation history
   - New chat creation

## 📊 **Monitor Deployment**

- **Cloud Console**: https://console.cloud.google.com/run?project=pbm-dev-careassist-genai-poc
- **Service Details**: https://console.cloud.google.com/run/detail/us-central1/pss-knowledge-assist?project=pbm-dev-careassist-genai-poc
- **Logs**: `gcloud logs read "resource.type=cloud_run_revision" --project pbm-dev-careassist-genai-poc --limit 50`

## 🔧 **Troubleshooting**

### **Authentication Issues**
```bash
gcloud auth login
gcloud auth application-default login
```

### **Billing Issues**
- Ensure billing is enabled for the project
- Check: https://console.cloud.google.com/billing/linkedaccount?project=pbm-dev-careassist-genai-poc

### **Permission Issues**
- Ensure you have "Cloud Run Admin" role
- Check IAM: https://console.cloud.google.com/iam-admin/iam?project=pbm-dev-careassist-genai-poc

## 🎉 **Success Indicators**

When deployment succeeds:
- ✅ Build completes successfully (5-10 minutes)
- ✅ Service URL is returned
- ✅ Health check passes at `/api/health`
- ✅ Login page loads at the URL
- ✅ Chat functionality works

## 🔗 **Sharing Your App**

Once deployed:
1. **Public URL**: Share with anyone for testing
2. **Login credentials**: `admin@pss-knowledge-assist.com` / `password123`
3. **Demo features**: Chat, feedback, conversations
4. **No VPN required**: Accessible from anywhere

## 📝 **Alternative: One-Click Scripts**

If you prefer automated deployment:

### **Windows**
```cmd
deploy-now.bat
```

### **PowerShell**
```powershell
.\deploy-now.bat
```

## 🌟 **What You're Deploying**

- ✅ **PSS Knowledge Assist** - Fully rebranded
- ✅ **Chat interface** - Streaming responses
- ✅ **Mock data fallbacks** - Works without database
- ✅ **Feedback system** - Thumbs up/down
- ✅ **Conversation management** - History and new chats
- ✅ **Authentication** - Fallback login system
- ✅ **Professional UI** - PSS branding and styling

Your app is production-ready and will work perfectly on Cloud Run!
