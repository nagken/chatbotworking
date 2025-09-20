import requests
import json

def test_login():
    """Test the login endpoint"""
    url = "http://127.0.0.1:8080/api/auth/login"
    
    # Test data
    login_data = {
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123",
        "remember_me": False
    }
    
    try:
        print(f"Testing login to: {url}")
        print(f"Data: {json.dumps(login_data, indent=2)}")
        
        response = requests.post(url, json=login_data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Login successful!")
            else:
                print(f"❌ Login failed: {result.get('message')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login()
