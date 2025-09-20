import json
import logging
import requests
from typing import Dict, Any, Optional, List
import google.auth
import google.auth.transport.requests
import requests
from datetime import datetime, timedelta


# Get default credentials (e.g., from service account or user login via gcloud)
print("Getting programmatic access token...")
credentials, project = google.auth.default()
# If the credentials are not already an access token, refresh them to get one
if not credentials.token:
    try:
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
    except Exception as e:
        print(f"Error refreshing credentials: {e}")
print(f"returning credentials: {str(credentials)}")



