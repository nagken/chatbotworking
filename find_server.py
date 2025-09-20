#!/usr/bin/env python3
"""
Quick script to find which port the server is running on
"""

import requests

def find_server():
    ports = [8080, 5000, 8000, 3000, 8001, 9000]
    
    print("🔍 Searching for CVS Pharmacy server...")
    
    for port in ports:
        try:
            url = f"http://localhost:{port}/api/health"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ Found server at: http://localhost:{port}")
                print(f"📋 Test links:")
                print(f"   Main UI: http://localhost:{port}/static/index.html")
                print(f"   Test UI: http://localhost:{port}/static/test_main_ui.html") 
                print(f"   Debug:   http://localhost:{port}/static/chat_debug.html")
                return port
        except:
            continue
    
    print("❌ No server found. Start with:")
    print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8080")
    return None

if __name__ == "__main__":
    result = find_server()
    exit(0 if result else 1)  # Return proper exit code
