import socket
import sys

def test_port(port):
    """Test if a port is available or in use"""
    try:
        # Test if port is available
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is in use (server might be running)")
            return True
        else:
            print(f"❌ Port {port} is not responding")
            return False
    except Exception as e:
        print(f"❌ Error testing port {port}: {e}")
        return False

def test_server_binding():
    """Test if we can bind to ports"""
    ports_to_test = [5000, 8000, 3000, 9000]
    
    print("Testing port availability...")
    
    for port in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', port))
            sock.close()
            print(f"✅ Port {port} is available for binding")
        except Exception as e:
            print(f"❌ Port {port} binding failed: {e}")

if __name__ == "__main__":
    print("=== CVS Pharmacy Server Diagnostics ===\n")
    
    # Test if server is responding
    print("1. Testing if server is responding...")
    test_port(5000)
    test_port(8000)
    
    print("\n2. Testing port binding capabilities...")
    test_server_binding()
    
    print("\n3. Network interface information...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        print(f"✅ Server responding on 127.0.0.1:5000 - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not responding on 127.0.0.1:5000: {e}")
    
    print("\nDone.")
