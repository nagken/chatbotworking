#!/usr/bin/env python3
"""
Quick server diagnostics and test
"""

import socket
import requests
import subprocess
import sys

def test_network_connectivity():
    """Test basic network connectivity"""
    print("=== Network Connectivity Test ===")
    
    # Test ports
    ports_to_test = [3000, 5000, 8000, 9000]
    
    for port in ports_to_test:
        try:
            # Test socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port}: Something is listening")
                
                # Test HTTP request
                try:
                    response = requests.get(f'http://127.0.0.1:{port}', timeout=3)
                    print(f"   HTTP Status: {response.status_code}")
                    if response.status_code == 200:
                        print(f"   🎉 SERVER FOUND ON PORT {port}!")
                        print(f"   URL: http://127.0.0.1:{port}")
                        print(f"   URL: http://localhost:{port}")
                        return port
                except Exception as e:
                    print(f"   HTTP failed: {e}")
            else:
                print(f"❌ Port {port}: Not listening")
                
        except Exception as e:
            print(f"❌ Port {port}: Error - {e}")
    
    print("\n❌ No active server found on any port")
    return None

def check_python_processes():
    """Check for running Python processes"""
    print("\n=== Python Processes ===")
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        if 'python.exe' in result.stdout:
            print("✅ Python processes found:")
            print(result.stdout)
        else:
            print("❌ No Python processes running")
    except Exception as e:
        print(f"❌ Could not check processes: {e}")

def main():
    print("CVS Pharmacy Knowledge Assist - Quick Diagnostics")
    print("=" * 50)
    
    # Test for active server
    active_port = test_network_connectivity()
    
    # Check processes
    check_python_processes()
    
    if active_port:
        print(f"\n🎉 SUCCESS! Server is running on port {active_port}")
        print(f"Open your browser to: http://localhost:{active_port}")
        print(f"Or try: http://127.0.0.1:{active_port}")
    else:
        print(f"\n❌ No server detected. Run start_server_python.py to start one.")

if __name__ == "__main__":
    main()
