# Google Cloud Credentials Setup

## Overview
The CVS Pharmacy Knowledge Assist chatbot uses Google Cloud's Gemini API for LLM responses. You need to provide credentials for this to work.

## Option 1: Service Account Key File (Recommended for Development)

### Step 1: Create a Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `pbm-dev-careassist-genai-poc`
3. Navigate to **IAM & Admin** → **Service Accounts**
4. Click **Create Service Account**
5. Name: `cvs-pharmacy-chatbot`
6. Description: `Service account for CVS Pharmacy Knowledge Assist chatbot`
7. Click **Create and Continue**

### Step 2: Assign Roles
Assign these roles to the service account:
- **Vertex AI User** (for Gemini API access)
- **BigQuery Data Viewer** (if using BigQuery)
- **Storage Object Viewer** (if accessing Cloud Storage)

### Step 3: Generate Key File
1. Click on your service account
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Download the key file
6. Save it as `credentials.json` in your project root: `c:\chatbotsep16\credentials.json`

### Step 4: Set Environment Variable
Create or update the `.env` file in your project root:

```bash
# Google Cloud Credentials
GOOGLE_APPLICATION_CREDENTIALS=c:\chatbotsep16\credentials.json

# Your project configuration
GCP_PROJECT_ID=pbm-dev-careassist-genai-poc
BILLING_PROJECT=pbm-dev-careassist-genai-poc
LOCATION=global
BASE_URL=https://geminidataanalytics.googleapis.com
```

## Option 2: Google Cloud CLI (Alternative)

### Install Google Cloud CLI
1. Download from: https://cloud.google.com/sdk/docs/install
2. Install and restart your terminal

### Authenticate
```bash
gcloud auth login
gcloud config set project pbm-dev-careassist-genai-poc
gcloud auth application-default login
```

## Option 3: Environment Variables (Production)

For production deployment, set these environment variables:
- `GOOGLE_APPLICATION_CREDENTIALS` (path to service account key)
- `GCP_PROJECT_ID`
- `BILLING_PROJECT`

## Verification

After setting up credentials, restart the server:
```bash
.\restart_server.bat
```

You should see:
```
INFO:app.services.llm_service:LLM Service initialized for project: pbm-dev-careassist-genai-poc
```

Instead of:
```
ERROR:app.services.llm_service:Failed to initialize LLM service...
```

## Security Notes

⚠️ **Important**: 
- Never commit `credentials.json` to version control
- Add `credentials.json` to `.gitignore`
- Use environment variables or secret managers in production
- Rotate service account keys regularly

## Troubleshooting

### Error: "Your default credentials were not found"
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON key file
- Or run `gcloud auth application-default login`

### Error: "Permission denied" 
- Verify your service account has the required roles
- Check that the project ID is correct

### Error: "API not enabled"
- Enable the Vertex AI API in Google Cloud Console
- Enable the Gemini Data Analytics API if needed
