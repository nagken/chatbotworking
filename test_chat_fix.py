import requests
import json

def test_document_chat():
    """Test the chat with document search functionality"""
    
    # Login first
    login_url = "http://127.0.0.1:8000/api/auth/login"
    login_data = {
        "email": "admin@cvs-pharmacy-knowledge-assist.com",
        "password": "admin123"
    }
    
    print("🔐 Logging in...")
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    # Test document search directly
    search_url = "http://127.0.0.1:8000/api/documents/search"
    search_params = {"query": "contraceptive coverage"}
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Testing document search...")
    response = requests.get(search_url, params=search_params, headers=headers)
    if response.status_code == 200:
        search_results = response.json()
        print(f"✅ Document search successful: {len(search_results)} results")
        for i, doc in enumerate(search_results[:2], 1):
            print(f"  {i}. {doc.get('filename', 'Unknown')} (Score: {doc.get('score', 0)})")
    else:
        print(f"❌ Document search failed: {response.status_code}")
        return
    
    # Test chat endpoint (non-streaming)
    chat_url = "http://127.0.0.1:8000/api/chat"
    chat_data = {
        "message": "What is contraceptive coverage?",
        "superclient": "CVS Pharmacy Knowledge Assist"
    }
    
    print("\n💬 Testing chat endpoint...")
    response = requests.post(chat_url, json=chat_data, headers=headers)
    if response.status_code == 200:
        chat_result = response.json()
        print("✅ Chat endpoint successful")
        print(f"📝 Response preview: {chat_result.get('message', '')[:200]}...")
        if 'Related Documents' in chat_result.get('message', ''):
            print("🎯 Response contains document references!")
        else:
            print("⚠️ Response does not contain document references")
    else:
        print(f"❌ Chat endpoint failed: {response.status_code}")

if __name__ == "__main__":
    test_document_chat()
