#!/usr/bin/env python3
"""
Simple server start script for debugging
"""

import subprocess
import sys
import os

def start_server():
    """Start the FastAPI server"""
    try:
        cmd = [
            "C:/Program Files/Python/311/python.exe",
            "-m", "uvicorn", 
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "5000",
            "--reload"
        ]
        
        print("Starting CVS Pharmacy Knowledge Assist server...")
        print(f"Command: {' '.join(cmd)}")
        print("Server will be available at: http://localhost:5000")
        print("Press Ctrl+C to stop")
        
        # Start the server
        subprocess.run(cmd, cwd="c:/chatbotsep16")
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    start_server()
