#!/usr/bin/env python3
"""
Test the login endpoint directly to diagnose authentication issues
"""

import asyncio
import aiohttp
import json

async def test_login_endpoint():
    """Test the login endpoint directly"""
    print("🔐 Testing Login Endpoint")
    print("=" * 50)
    
    url = "http://127.0.0.1:5000/api/auth/login"
    
    # Test credentials from the frontend auto-fill
    credentials = {
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123",
        "remember_me": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📤 Testing login endpoint: {url}")
            print(f"📧 Using credentials: {credentials['email']}")
            
            async with session.post(url, json=credentials) as response:
                print(f"📊 Response status: {response.status}")
                print(f"📋 Response headers: {dict(response.headers)}")
                
                try:
                    response_data = await response.json()
                    print(f"📥 Response data:")
                    print(json.dumps(response_data, indent=2))
                    
                    if response_data.get('success'):
                        print(f"✅ Login successful!")
                        session_token = response_data.get('session_token')
                        if session_token:
                            print(f"🔑 Session token: {session_token[:20]}...")
                        user_info = response_data.get('user', {})
                        print(f"👤 User: {user_info.get('username')} ({user_info.get('email')})")
                    else:
                        print(f"❌ Login failed: {response_data.get('message')}")
                        
                except Exception as json_error:
                    response_text = await response.text()
                    print(f"❌ JSON parse error: {json_error}")
                    print(f"📄 Raw response: {response_text}")
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

async def test_health_endpoint():
    """Test the health endpoint to verify server is responding"""
    print("\n🏥 Testing Health Endpoint")
    print("=" * 50)
    
    url = "http://127.0.0.1:5000/api/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"📊 Health status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                else:
                    text = await response.text()
                    print(f"❌ Health check failed: {text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

async def main():
    await test_health_endpoint()
    await test_login_endpoint()

if __name__ == "__main__":
    asyncio.run(main())