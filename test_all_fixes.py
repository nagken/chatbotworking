#!/usr/bin/env python3
"""
Comprehensive test script for CVS Pharmacy Knowledge Assist
Tests all the fixes implemented for document search and UI display
"""

import requests
import json
import time
import sys
from typing import Optional

class CVSPharmacyTester:
    def __init__(self):
        self.base_url = None
        self.token = None
        self.test_results = {
            "server_health": False,
            "login": False,
            "non_streaming_chat": False,
            "document_search": False,
            "streaming_chat": False,
            "frontend_files": False
        }

    def find_server(self) -> Optional[str]:
        """Find which port the server is running on"""
        ports = [8080, 5000, 8000, 3000, 8001]
        
        print("🔍 Searching for CVS Pharmacy server...")
        
        for port in ports:
            try:
                url = f"http://localhost:{port}"
                response = requests.get(f"{url}/api/health", timeout=3)
                if response.status_code == 200:
                    print(f"✅ Found server at: {url}")
                    return url
            except:
                continue
        
        print("❌ No server found on common ports")
        return None

    def test_server_health(self) -> bool:
        """Test server health endpoint"""
        print("\n🏥 Testing server health...")
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Server health OK")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                if 'pdf_service' in health_data:
                    print(f"   PDF Service: {health_data['pdf_service']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def test_login(self) -> bool:
        """Test authentication"""
        print("\n🔐 Testing login...")
        
        login_data = {
            "email": "john.smith@cvshealth.com",
            "password": "password123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data, timeout=10)
            if response.status_code == 200:
                login_result = response.json()
                self.token = login_result.get("access_token")
                if self.token:
                    print(f"✅ Login successful")
                    print(f"   User: {login_result.get('user', {}).get('email', 'unknown')}")
                    return True
                else:
                    print(f"❌ No access token in response")
                    return False
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_document_search(self) -> bool:
        """Test document search API directly"""
        print("\n📚 Testing document search API...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"query": "contraceptive coverage", "limit": 3}
        
        try:
            response = requests.get(f"{self.base_url}/api/documents/search", 
                                  headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                docs = response.json()
                if isinstance(docs, list) and len(docs) > 0:
                    print(f"✅ Document search working")
                    print(f"   Found {len(docs)} documents")
                    print(f"   Top result: {docs[0].get('filename', 'unknown')}")
                    print(f"   Relevance: {docs[0].get('relevance_score', 0)}")
                    return True
                else:
                    print(f"❌ No documents found")
                    return False
            else:
                print(f"❌ Document search failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Document search error: {e}")
            return False

    def test_non_streaming_chat(self) -> bool:
        """Test the fixed non-streaming chat endpoint"""
        print("\n💬 Testing non-streaming chat (FIXED)...")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        chat_data = {
            "message": "What is contraceptive coverage?",
            "superclient": "CVS Pharmacy"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/chat", 
                                   json=chat_data, headers=headers, timeout=30)
            if response.status_code == 200:
                chat_result = response.json()
                
                if isinstance(chat_result, dict) and chat_result.get('success'):
                    print(f"✅ Non-streaming chat working")
                    
                    message = str(chat_result.get('message', ''))
                    has_documents = 'Related Documents' in message
                    
                    print(f"   Success: {chat_result.get('success')}")
                    print(f"   Has document results: {'✅' if has_documents else '❌'}")
                    print(f"   Response length: {len(message)} chars")
                    
                    if has_documents:
                        doc_start = message.find('Related Documents')
                        snippet = message[doc_start:doc_start+150]
                        print(f"   Document snippet: {snippet}...")
                    
                    return True
                else:
                    print(f"❌ Invalid response format or unsuccessful")
                    print(f"   Response: {chat_result}")
                    return False
            else:
                print(f"❌ Non-streaming chat failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Non-streaming chat error: {e}")
            return False

    def test_frontend_files(self) -> bool:
        """Test that frontend files are accessible"""
        print("\n🌐 Testing frontend files...")
        
        files_to_test = [
            "/static/index.html",
            "/static/test_main_ui.html", 
            "/static/chat_debug.html",
            "/static/js/message-renderer.js",
            "/static/styles.css"
        ]
        
        all_good = True
        for file_path in files_to_test:
            try:
                response = requests.get(f"{self.base_url}{file_path}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {file_path}")
                else:
                    print(f"   ❌ {file_path} - {response.status_code}")
                    all_good = False
            except Exception as e:
                print(f"   ❌ {file_path} - {e}")
                all_good = False
        
        return all_good

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("=" * 60)
        print("  CVS PHARMACY KNOWLEDGE ASSIST - COMPREHENSIVE TEST")
        print("=" * 60)
        
        # Find server
        self.base_url = self.find_server()
        if not self.base_url:
            print("\n❌ Cannot find running server")
            print("💡 Start server with: python -m uvicorn app.main:app --host 127.0.0.1 --port 8080")
            return False
        
        # Run tests
        self.test_results["server_health"] = self.test_server_health()
        self.test_results["login"] = self.test_login()
        
        if self.test_results["login"]:
            self.test_results["document_search"] = self.test_document_search()
            self.test_results["non_streaming_chat"] = self.test_non_streaming_chat()
        
        self.test_results["frontend_files"] = self.test_frontend_files()
        
        # Summary
        self.print_summary()
        
        return all(self.test_results.values())

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("  TEST SUMMARY")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if all(self.test_results.values()):
            print("\n🎉 ALL TESTS PASSED!")
            print("\n📋 Ready to test manually:")
            print(f"   1. Open: {self.base_url}/static/test_main_ui.html")
            print(f"   2. Login: john.smith@cvshealth.com / password123")
            print(f"   3. Ask: 'What is contraceptive coverage?'")
            print(f"   4. Look for: '📚 Related Documents Found' section")
        else:
            print("\n⚠️ Some tests failed - check the details above")

if __name__ == "__main__":
    tester = CVSPharmacyTester()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Ready for deployment.")
    else:
        print("⚠️ Some tests failed. Please review and fix issues.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
