#!/usr/bin/env python3
"""
Setup BigQuery dataset and tables for CVS Pharmacy webapp
"""

import os
import subprocess
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict
import google.auth
from google.oauth2.credentials import Credentials

def get_gcloud_credentials():
    """Get credentials using gcloud access token"""
    try:
        # Get access token from gcloud
        gcloud_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Google", "Cloud SDK", "google-cloud-sdk", "bin", "gcloud.cmd")
        
        if os.path.exists(gcloud_path):
            result = subprocess.run([gcloud_path, "auth", "print-access-token"], 
                                 capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                access_token = result.stdout.strip()
                
                # Create credentials with the access token
                credentials = Credentials(token=access_token)
                return credentials
            else:
                print(f"Failed to get access token from gcloud: {result.stderr}")
        else:
            print(f"gcloud not found at: {gcloud_path}")
                    
        return None
        
    except Exception as e:
        print(f"Error obtaining credentials: {e}")
        return None

def setup_bigquery():
    """Setup BigQuery dataset and tables"""
    
    project_id = "flawless-acre-401603"
    dataset_id = "cvs_pharmacy_data"
    
    # Get credentials
    credentials = get_gcloud_credentials()
    if not credentials:
        print("❌ Failed to get credentials")
        return False
    
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id, credentials=credentials)
    
    # Create dataset
    dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
    dataset.location = "US"
    dataset.description = "CVS Pharmacy Knowledge Assist Data"
    
    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset {client.project}.{dataset.dataset_id}")
    except Conflict:
        print(f"ℹ️  Dataset {client.project}.{dataset_id} already exists")
    except Exception as e:
        print(f"❌ Error creating dataset: {e}")
        return False
    
    # Create documents table
    table_id = f"{project_id}.{dataset_id}.documents"
    
    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Document storage for CVS Pharmacy Knowledge Base"
    
    try:
        table = client.create_table(table, timeout=30)
        print(f"✅ Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Conflict:
        print(f"ℹ️  Table {table_id} already exists")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
    
    # Create conversations table  
    table_id = f"{project_id}.{dataset_id}.conversations"
    
    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Conversation storage for CVS Pharmacy chat sessions"
    
    try:
        table = client.create_table(table, timeout=30)
        print(f"✅ Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Conflict:
        print(f"ℹ️  Table {table_id} already exists")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
        
    # Create messages table
    table_id = f"{project_id}.{dataset_id}.messages"
    
    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("conversation_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("role", "STRING", mode="REQUIRED"),  # 'user' or 'assistant'
        bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Message storage for CVS Pharmacy chat conversations"
    
    try:
        table = client.create_table(table, timeout=30)
        print(f"✅ Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Conflict:
        print(f"ℹ️  Table {table_id} already exists")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
    
    print("\n🎉 BigQuery setup completed successfully!")
    print(f"📊 Dataset: {project_id}.{dataset_id}")
    print("📋 Tables: documents, conversations, messages")
    
    return True

if __name__ == "__main__":
    success = setup_bigquery()
    if success:
        print("\n✅ BigQuery is ready for the CVS Pharmacy webapp!")
    else:
        print("\n❌ BigQuery setup failed!")