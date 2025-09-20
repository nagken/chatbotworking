import requests
import json

def test_login():
    url = "http://127.0.0.1:8080/api/auth/login"
    data = {
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123",
        "remember_me": False
    }
    
    print(f"Testing login to: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"Response JSON:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print("\n✅ LOGIN SUCCESS!")
            else:
                print(f"\n❌ LOGIN FAILED: {result.get('message')}")
                
        except json.JSONDecodeError:
            print(f"Raw response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_login()
