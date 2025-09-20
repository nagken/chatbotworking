#!/usr/bin/env python3
"""
Force restart server and test routes
"""
import os
import sys
import subprocess
import time
import requests

# Change to project directory
os.chdir(r'c:\cvssep9')
sys.path.insert(0, os.getcwd())

def kill_python_processes():
    """Try to kill any existing Python processes"""
    try:
        result = subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                              capture_output=True, text=True)
        print(f"Kill result: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    except Exception as e:
        print(f"Error killing processes: {e}")

def start_server():
    """Start the server"""
    print("Starting server...")
    cmd = [
        r'C:\Program Files\Python\311\python.exe',
        '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', '8080',
        '--reload'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Start the server in background
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True)
        return process
    except Exception as e:
        print(f"Error starting server: {e}")
        return None

def test_routes():
    """Test the routes"""
    base_url = "http://127.0.0.1:8080"
    
    routes_to_test = [
        "/health",
        "/api/health",
        "/test-login",
        "/"
    ]
    
    print("Waiting for server to start...")
    time.sleep(5)
    
    for route in routes_to_test:
        url = f"{base_url}{route}"
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {route}: {response.status_code}")
            if route == "/test-login" and response.status_code == 200:
                print("   🎉 Test login page is working!")
        except Exception as e:
            print(f"❌ {route}: {e}")

def main():
    print("=== Force Server Restart Test ===")
    
    # Kill existing processes
    print("\n1. Killing existing Python processes...")
    kill_python_processes()
    
    # Wait a bit
    time.sleep(2)
    
    # Start server
    print("\n2. Starting new server...")
    process = start_server()
    
    if process:
        try:
            # Test routes
            print("\n3. Testing routes...")
            test_routes()
            
            print(f"\n4. Server is running. Test at: http://127.0.0.1:8080/test-login")
            print("Press Ctrl+C to stop")
            
            # Keep server running
            process.wait()
            
        except KeyboardInterrupt:
            print("\n✅ Stopping server...")
            process.terminate()
            process.wait()
    else:
        print("❌ Failed to start server")

if __name__ == "__main__":
    main()
