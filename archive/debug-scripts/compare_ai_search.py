#!/usr/bin/env python3

import requests
import json

def test_ai_vs_search():
    """Compare what document search returns vs what AI outputs"""
    
    session = requests.Session()
    
    # Login
    login_data = {"email": "admin@pss-knowledge-assist.com", "password": "admin123"}
    login_response = session.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed")
        return
        
    print("✅ Login successful")
    
    # 1. Test what document search API returns
    print("\n=== DOCUMENT SEARCH API RESULTS ===")
    search_response = session.get("http://127.0.0.1:5000/api/documents/search?query=contraceptive%20coverage&limit=5")
    
    if search_response.status_code == 200:
        search_data = search_response.json()
        print(f"Search found {len(search_data.get('results', []))} documents:")
        
        for i, doc in enumerate(search_data.get('results', [])[:3]):
            filename = doc.get('filename', 'Unknown')
            print(f"  {i+1}. {filename}")
            
            # Test if this exact filename works as a link
            doc_url = f"http://127.0.0.1:5000/documents/{filename}"
            try:
                doc_response = session.head(doc_url, timeout=3)
                status = "✅ WORKS" if doc_response.status_code == 200 else f"❌ {doc_response.status_code}"
            except:
                status = "❌ ERROR"
            print(f"     Link test: {status}")
    
    # 2. Test what AI chat returns
    print("\n=== AI CHAT RESPONSE ===")
    chat_data = {
        "message": "What is contraceptive coverage? Include specific document references.",
        "conversation_id": None
    }
    
    chat_response = session.post("http://127.0.0.1:5000/api/chat/stream", json=chat_data, stream=True, timeout=30)
    
    if chat_response.status_code == 200:
        ai_insights = ""
        for line in chat_response.iter_lines():
            if line:
                try:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_text = line_text[6:]
                        if data_text.strip() and data_text != '[DONE]':
                            chunk = json.loads(data_text)
                            
                            if chunk.get('type') == 'system_message' and chunk.get('message_type') == 'insights':
                                ai_insights = chunk.get('data', {}).get('ai_insights', '')
                                break
                except:
                    continue
        
        if ai_insights:
            print("AI Response received. Analyzing document references...")
            
            # Extract document references from AI response
            import re
            
            # Look for document patterns
            doc_patterns = [
                r'Document \d+: ([^)]+\.(?:pdf|docx?))',
                r'File: ([^)]+\.(?:pdf|docx?))',
                r'([^<\s)]+\.(?:pdf|docx?))'
            ]
            
            ai_mentioned_docs = set()
            for pattern in doc_patterns:
                matches = re.findall(pattern, ai_insights, re.IGNORECASE)
                ai_mentioned_docs.update(matches)
            
            print(f"AI mentioned these documents:")
            for doc in ai_mentioned_docs:
                print(f"  - {doc}")
                
                # Test if AI's referenced filename works
                doc_url = f"http://127.0.0.1:5000/documents/{doc}"
                try:
                    doc_response = session.head(doc_url, timeout=3)
                    status = "✅ WORKS" if doc_response.status_code == 200 else f"❌ {doc_response.status_code}"
                except:
                    status = "❌ ERROR"
                print(f"    Link test: {status}")
        else:
            print("❌ No AI insights received")
    else:
        print(f"❌ Chat failed: {chat_response.status_code}")

if __name__ == "__main__":
    test_ai_vs_search()