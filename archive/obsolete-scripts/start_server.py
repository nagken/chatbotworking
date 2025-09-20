#!/usr/bin/env python3
"""
Simple server startup script for PSS Knowledge Assist
"""
import os
import sys
import subprocess

def main():
    # Change to the correct directory
    os.chdir(r'c:\cvssep9')
    
    # Start the server
    cmd = [
        sys.executable, 
        '-m', 'uvicorn', 
        'app.main:app', 
        '--reload', 
        '--host', '0.0.0.0', 
        '--port', '8000'
    ]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
