# 🚀 Quick Deployment Guide - PSS Knowledge Assist

## For Public/External Testing

### **Recommended: Google Cloud Run** (Free tier available)

#### **Option A: One-Click Script** (5 minutes)
1. **Install Google Cloud CLI**: https://cloud.google.com/sdk/docs/install
2. **Set up project**:
   ```bash
   gcloud auth login
   gcloud projects create pss-knowledge-assist --name="PSS Knowledge Assist"
   gcloud config set project pss-knowledge-assist
   ```
3. **Deploy**:
   ```bat
   deploy-cloud-run.bat
   ```
4. **Done!** You'll get a public URL like: `https://pss-knowledge-assist-xxx-uc.a.run.app`

#### **Option B: GitHub Actions** (10 minutes setup, then automatic)
1. **Push to GitHub** (if not already done)
2. **Create Google Cloud Project**: https://console.cloud.google.com
3. **Create Service Account**:
   - Go to IAM & Admin > Service Accounts
   - Create new service account
   - Add roles: Cloud Run Admin, Storage Admin, Service Account User
   - Generate JSON key
4. **Add GitHub Secrets**:
   - Repository Settings > Secrets and Variables > Actions
   - Add: `GCP_PROJECT_ID` (your project ID)
   - Add: `GCP_SERVICE_ACCOUNT_KEY` (paste JSON key content)
5. **Push to main branch** - auto-deploys!

### **Alternative: Railway** (Easiest, 2 minutes)
1. Go to: https://railway.app
2. Sign up with GitHub
3. Click "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Docker and deploys
6. **Done!** Get public URL instantly

### **Alternative: Render** (Free tier)
1. Go to: https://render.com
2. Sign up with GitHub
3. "New" > "Web Service"
4. Connect your GitHub repo
5. Runtime: Docker
6. **Deploy** - get public URL

## For Local Testing

### **Docker (Recommended)**
```bat
deploy.bat
```
- Opens at: http://localhost:8080
- Includes automated testing
- Works offline

### **Python Direct**
```bat
run_server.bat
```
- Opens at: http://localhost:8000
- For development/debugging
- Requires Python environment

## 🔧 Troubleshooting

### **Docker Issues**
- Ensure Docker Desktop is running
- Check: `docker version`
- Restart Docker if needed

### **Cloud Deployment Issues**
- Check Google Cloud CLI: `gcloud version`
- Verify project: `gcloud config get-value project`
- Check billing is enabled for the project

### **GitHub Actions Issues**
- Verify secrets are set correctly
- Check Actions tab for error details
- Ensure service account has proper permissions

## 📊 Testing Checklist

After deployment, test these features:
- [ ] Login works (test user: `test@example.com` / `password123`)
- [ ] Chat interface loads
- [ ] Send a message and get response
- [ ] Thumbs up/down feedback works
- [ ] Conversation history appears in sidebar
- [ ] New chat creates new conversation

## 🌐 Sharing Your App

Once deployed to cloud:
1. **Share the URL** - anyone can access
2. **Test credentials**: `test@example.com` / `password123`
3. **Demo features**: 
   - Ask: "What job aids are available?"
   - Ask: "How do I handle customer complaints?"
   - Test feedback buttons
   - Create multiple conversations

## 🔒 Security Notes

- Current setup uses mock authentication (perfect for testing)
- Default test user is available for demos
- For production, implement proper user management
- Consider adding access restrictions if needed
