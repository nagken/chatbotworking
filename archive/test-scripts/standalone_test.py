#!/usr/bin/env python3
"""
Standalone test server - starts its own FastAPI instance to test login
"""
import asyncio
import os
import sys
import threading
import time
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Change to project directory and add to path
os.chdir(r'c:\cvssep9')
sys.path.insert(0, os.getcwd())

def create_test_app():
    """Create a minimal test app with just the login test route"""
    app = FastAPI(title="Test Server")
    
    @app.get("/test-login")
    async def test_login_page():
        """Simple test login page"""
        html_content = """
<!DOCTYPE html>
<html>
<head><title>Test Login - PSS Knowledge Assist</title></head>
<body>
    <h1>Test Login Page</h1>
    <p>If you can see this, the test-login route is working!</p>
    <button onclick="testBasic()">Test Basic Function</button>
    <div id="result"></div>
    
    <script>
        function testBasic() {
            document.getElementById('result').innerHTML = '✅ JavaScript is working!';
        }
    </script>
</body>
</html>
        """
        return HTMLResponse(content=html_content)
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "message": "Test server is running"}
    
    return app

def run_test_server():
    """Run the test server in a thread"""
    import uvicorn
    app = create_test_app()
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

def test_endpoints():
    """Test the endpoints"""
    base_url = "http://127.0.0.1:8001"
    
    # Wait for server to start
    print("Waiting for test server to start...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Test server is running!")
                break
        except:
            time.sleep(1)
    else:
        print("❌ Test server failed to start")
        return
    
    # Test the test-login endpoint
    try:
        response = requests.get(f"{base_url}/test-login", timeout=5)
        print(f"✅ /test-login: {response.status_code}")
        if "Test Login Page" in response.text:
            print("✅ Test login page content is correct")
        else:
            print("❌ Test login page content is wrong")
            
    except Exception as e:
        print(f"❌ /test-login failed: {e}")

if __name__ == "__main__":
    print("Starting standalone test server on port 8001...")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_test_server, daemon=True)
    server_thread.start()
    
    # Test endpoints
    time.sleep(2)  # Give server time to start
    test_endpoints()
    
    print("\nTest server running at http://127.0.0.1:8001/test-login")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ Test complete")
