#!/usr/bin/env python3
"""
Quick test to see what routes are defined and if the app starts
"""
import os
import sys

# Change to correct directory
os.chdir(r'c:\cvssep9')
sys.path.insert(0, os.getcwd())

try:
    print("1. Testing basic imports...")
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    from app.main import app
    print("✅ App imported successfully")
    
    print(f"✅ App title: {app.title}")
    
    print("\n2. Checking routes...")
    for route in app.routes:
        print(f"   {route.methods} {route.path}")
    
    print("\n3. Testing /test-login route specifically...")
    test_login_routes = [r for r in app.routes if hasattr(r, 'path') and '/test-login' in r.path]
    print(f"   Found {len(test_login_routes)} test-login routes")
    for route in test_login_routes:
        print(f"   - {route.methods} {route.path}")
    
    print("\n4. Starting server manually...")
    import uvicorn
    print("Press Ctrl+C to stop the server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    
except KeyboardInterrupt:
    print("\n✅ Server stopped by user")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
