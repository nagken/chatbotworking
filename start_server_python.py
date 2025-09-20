#!/usr/bin/env python3
"""
Direct Python server starter for CVS Pharmacy Knowledge Assist
This bypasses batch file issues and starts the server directly
"""

import subprocess
import socket
import sys
import time
import os

def check_port_available(host, port):
    """Check if a port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0  # True if port is available (connection failed)
    except:
        return False

def find_available_port(start_port=3000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if check_port_available('127.0.0.1', port):
            return port
    return None

def start_server():
    """Start the CVS Pharmacy Knowledge Assist server"""
    print("=" * 50)
    print("CVS Pharmacy Knowledge Assist - Python Starter")
    print("=" * 50)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    # Kill existing Python processes
    print("\nKilling existing Python processes...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                      capture_output=True, check=False)
        time.sleep(2)
    except:
        pass
    
    # Find available port
    print("\nFinding available port...")
    ports_to_try = [3000, 5000, 8000, 9000, 4000, 6000, 7000]
    
    for port in ports_to_try:
        if check_port_available('127.0.0.1', port):
            print(f"✅ Port {port} is available")
            
            # Start the server
            print(f"\nStarting server on http://127.0.0.1:{port}")
            print(f"Also available at: http://localhost:{port}")
            print("\nPress Ctrl+C to stop the server")
            print("-" * 50)
            
            try:
                # Use the full Python path
                python_path = r"C:\Program Files\Python\311\python.exe"
                cmd = [
                    python_path, "-m", "uvicorn", 
                    "app.main:app", 
                    "--host", "127.0.0.1", 
                    "--port", str(port), 
                    "--reload"
                ]
                
                subprocess.run(cmd, check=True)
                
            except KeyboardInterrupt:
                print("\n\nServer stopped by user")
                return
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to start server on port {port}: {e}")
                continue
            except FileNotFoundError:
                print("❌ Python not found at expected path")
                print("Trying system Python...")
                try:
                    cmd[0] = "python"
                    subprocess.run(cmd, check=True)
                except:
                    print("❌ Could not find Python interpreter")
                    return
            
            return
        else:
            print(f"❌ Port {port} is busy")
    
    print("❌ No available ports found!")
    print("Please close other applications and try again")

if __name__ == "__main__":
    start_server()
