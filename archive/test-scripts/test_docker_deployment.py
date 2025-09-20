#!/usr/bin/env python3
"""
PSS Knowledge Assist - Docker Deployment Test
Tests all aspects of the Dockerized application
"""

import requests
import time
import json
import sys
from datetime import datetime

class DockerTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{status_emoji.get(status, 'ℹ️')} [{timestamp}] {message}")
        
        self.test_results.append({
            "timestamp": timestamp,
            "status": status,
            "message": message
        })
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                self.log("Health endpoint is working", "SUCCESS")
                return True
            else:
                self.log(f"Health endpoint returned {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Health endpoint failed: {e}", "ERROR")
            return False
    
    def test_static_files(self):
        """Test static file serving"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200 and "PSS Knowledge Assist" in response.text:
                self.log("Static files are being served correctly", "SUCCESS")
                return True
            else:
                self.log("Static files not serving correctly", "ERROR")
                return False
        except Exception as e:
            self.log(f"Static file test failed: {e}", "ERROR")
            return False
    
    def test_quick_test_endpoint(self):
        """Test the comprehensive quick-test endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/quick-test", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log("Quick test endpoint passed all checks", "SUCCESS")
                    return True
                else:
                    self.log(f"Quick test failed: {data.get('message', 'Unknown error')}", "ERROR")
                    return False
            else:
                self.log(f"Quick test endpoint returned {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Quick test endpoint failed: {e}", "ERROR")
            return False
    
    def test_mock_authentication(self):
        """Test authentication with mock credentials"""
        try:
            # Test login endpoint
            login_data = {
                "username": "admin@pss-knowledge-assist.com",
                "password": "admin123",
                "remember_me": False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("session_token"):
                    self.log("Mock authentication is working", "SUCCESS")
                    return data.get("session_token")
                else:
                    self.log("Authentication failed - no token received", "ERROR")
                    return None
            else:
                self.log(f"Authentication endpoint returned {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"Authentication test failed: {e}", "ERROR")
            return None
    
    def test_chat_functionality(self, session_token):
        """Test chat functionality with mock responses"""
        try:
            headers = {"Authorization": f"Bearer {session_token}"}
            chat_data = {
                "message": "Docker test message",
                "conversation_id": None
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=chat_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log("Chat functionality is working", "SUCCESS")
                    return data.get("conversation_id")
                else:
                    self.log("Chat failed - no success in response", "ERROR")
                    return None
            else:
                self.log(f"Chat endpoint returned {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"Chat test failed: {e}", "ERROR")
            return None
    
    def test_conversations_endpoint(self, session_token):
        """Test conversations listing"""
        try:
            headers = {"Authorization": f"Bearer {session_token}"}
            response = self.session.get(
                f"{self.base_url}/api/conversations",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "conversations" in data:
                    self.log(f"Conversations endpoint working - {len(data['conversations'])} conversations", "SUCCESS")
                    return True
                else:
                    self.log("Conversations endpoint missing data", "ERROR")
                    return False
            else:
                self.log(f"Conversations endpoint returned {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Conversations test failed: {e}", "ERROR")
            return False
    
    def wait_for_application(self, max_attempts=30):
        """Wait for the application to be ready"""
        self.log("Waiting for application to be ready...")
        
        for attempt in range(max_attempts):
            try:
                response = self.session.get(f"{self.base_url}/api/health", timeout=3)
                if response.status_code == 200:
                    self.log(f"Application ready after {attempt + 1} attempts", "SUCCESS")
                    return True
            except:
                pass
            
            if attempt < max_attempts - 1:
                time.sleep(2)
        
        self.log("Application failed to become ready within timeout", "ERROR")
        return False
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        self.log("🚀 Starting PSS Knowledge Assist Docker Test Suite")
        self.log("=" * 60)
        
        # Wait for application
        if not self.wait_for_application():
            return False
        
        # Test 1: Health endpoint
        if not self.test_health_endpoint():
            return False
        
        # Test 2: Static files
        if not self.test_static_files():
            return False
        
        # Test 3: Quick test endpoint
        if not self.test_quick_test_endpoint():
            return False
        
        # Test 4: Authentication
        session_token = self.test_mock_authentication()
        if not session_token:
            return False
        
        # Test 5: Chat functionality
        conversation_id = self.test_chat_functionality(session_token)
        if not conversation_id:
            return False
        
        # Test 6: Conversations endpoint
        if not self.test_conversations_endpoint(session_token):
            return False
        
        # All tests passed
        self.log("=" * 60)
        self.log("🎉 All tests passed! Docker deployment is working correctly", "SUCCESS")
        return True
    
    def generate_report(self):
        """Generate test report"""
        success_count = len([r for r in self.test_results if r["status"] == "SUCCESS"])
        error_count = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Successful tests: {success_count}")
        print(f"❌ Failed tests: {error_count}")
        print(f"📋 Total tests: {len(self.test_results)}")
        print("=" * 60)
        
        if error_count > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "ERROR":
                    print(f"   {result['timestamp']} - {result['message']}")
        
        return error_count == 0

def main():
    """Main test function"""
    print("🐳 PSS Knowledge Assist - Docker Deployment Tester")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = DockerTester()
    
    try:
        success = tester.run_full_test_suite()
        overall_success = tester.generate_report()
        
        if overall_success:
            print("\n🎯 RESULT: Docker deployment is fully functional!")
            sys.exit(0)
        else:
            print("\n💥 RESULT: Some tests failed - check logs above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏸️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
