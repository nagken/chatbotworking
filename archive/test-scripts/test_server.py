#!/usr/bin/env python3
"""
Test script to validate the main.py file and check for import errors
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def test_imports():
    """Test if we can import the main app"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from app.main import app
        print("✅ Successfully imported FastAPI app")
        
        # Check if app is configured correctly
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        
        # Check routes
        routes = [route.path for route in app.routes]
        print(f"✅ Available routes: {len(routes)}")
        for route in routes:
            print(f"   - {route}")
            
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_server():
    """Try to start server manually"""
    try:
        print("\nTesting manual server startup...")
        import uvicorn
        from app.main import app
        
        print("✅ Uvicorn and app imported successfully")
        print("Starting server on http://0.0.0.0:8000")
        print("Press Ctrl+C to stop")
        
        # Start server
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
        
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if test_imports():
        test_manual_server()
