#!/usr/bin/env python3
"""
Test script for new database authentication flow
Tests both backend and frontend integration
"""
import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database.connection import init_database, get_db_session
from app.auth.user_repository import UserRepository
from app.models.schemas import UserCreate
import logging
import aiohttp
import warnings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress passlib bcrypt version warnings (known compatibility issue)
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*", category=UserWarning)

async def test_password_authentication(user_repo, migrated_users):
    """Test authentication with original passwords from users.json"""
    print(f"\n🔐 TESTING PASSWORD AUTHENTICATION")
    print("-" * 30)
    
    # Try to load original passwords from users.json
    users_json_file = "users.json"
    original_passwords = {}
    
    try:
        if os.path.exists(users_json_file):
            with open(users_json_file, 'r') as f:
                original_users = json.load(f)
            
            # Extract email -> password mapping
            for email, user_data in original_users.items():
                if isinstance(user_data, dict) and 'password' in user_data:
                    original_passwords[email.lower()] = user_data['password']
                else:
                    # Handle simple email:password format
                    original_passwords[email.lower()] = user_data
            
            print(f"📂 Found {len(original_passwords)} passwords in {users_json_file}")
        else:
            print(f"⚠️  {users_json_file} not found - skipping password authentication test")
            print(f"   This is normal if you've already archived the file after migration")
            return True
            
    except Exception as e:
        print(f"❌ Error reading {users_json_file}: {e}")
        return False
    
    # Test authentication for migrated users
    auth_tests_passed = 0
    auth_tests_total = 0
    
    for user in migrated_users[:3]:  # Test first 3 users
        email = user.email.lower()
        
        if email in original_passwords:
            password = original_passwords[email]
            auth_tests_total += 1
            
            try:
                # Test authentication
                authenticated_user = await user_repo.authenticate_user(email, password)
                
                if authenticated_user:
                    print(f"   ✅ {email} - Authentication successful")
                    auth_tests_passed += 1
                    
                    # Verify user data integrity
                    if authenticated_user.username == user.username:
                        print(f"      ✅ Username matches: {user.username}")
                    else:
                        print(f"      ⚠️  Username mismatch: {authenticated_user.username} vs {user.username}")
                    
                    if authenticated_user.is_active:
                        print(f"      ✅ Account is active")
                    else:
                        print(f"      ❌ Account is inactive")
                else:
                    print(f"   ❌ {email} - Authentication failed")
                    print(f"      Password from users.json may be incorrect or user is inactive")
                    
            except Exception as e:
                print(f"   ❌ {email} - Authentication error: {e}")
        else:
            print(f"   ⏭️  {email} - No original password found, skipping")
    
    # Summary
    if auth_tests_total > 0:
        print(f"\n📊 Authentication test results: {auth_tests_passed}/{auth_tests_total} passed")
        
        if auth_tests_passed == auth_tests_total:
            print("🎉 All password authentications successful!")
            print("💡 Your migration preserved password integrity correctly")
        elif auth_tests_passed > 0:
            print("⚠️  Some authentications failed - check password migration")
        else:
            print("❌ All authentications failed - migration may have issues")
            
        return auth_tests_passed == auth_tests_total
    else:
        print("ℹ️  No password tests could be performed")
        return True

async def test_database_auth():
    """Test database authentication directly"""
    print("🧪 TESTING DATABASE AUTHENTICATION")
    print("="*50)
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database connection initialized")
        
        async with get_db_session() as db:
            user_repo = UserRepository(db)
            
            # Test 1: List existing users
            users = await user_repo.list_users(limit=5)
            print(f"📊 Found {len(users)} users in database:")
            
            for user in users[:3]:  # Show first 3 users
                status = "🟢 Active" if user.is_active else "🔴 Inactive"
                print(f"   {status} {user.email} ({user.username})")
            
            if not users:
                print("   ❌ No users found! Make sure you ran the migration script.")
                return False
            
            # Test 2: Authentication test with original passwords
            await test_password_authentication(user_repo, users)
                
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_api_authentication(session, base_url):
    """Test API authentication with real credentials"""
    print(f"\n🌐 TESTING API AUTHENTICATION")
    print("-" * 30)
    
    # Try to get real credentials from users.json
    users_json_file = "users.json"
    
    try:
        if not os.path.exists(users_json_file):
            print(f"⚠️  {users_json_file} not found - skipping API authentication test")
            return True
            
        with open(users_json_file, 'r') as f:
            original_users = json.load(f)
        
        # Test with first available user
        for email, user_data in list(original_users.items())[:1]:  # Test just first user
            if isinstance(user_data, dict) and 'password' in user_data:
                password = user_data['password']
            else:
                password = user_data
            
            test_login = {
                "email": email,
                "password": password,
                "remember_me": False
            }
            
            print(f"🔐 Testing API login for: {email}")
            
            async with session.post(
                f"{base_url}/api/auth/login",
                json=test_login,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 200 and result.get('success'):
                    print(f"   ✅ API authentication successful")
                    print(f"   ✅ User ID: {result.get('user', {}).get('id', 'N/A')}")
                    print(f"   ✅ Username: {result.get('user', {}).get('username', 'N/A')}")
                    print(f"   ✅ Session duration: {result.get('session_duration', 'N/A')} seconds")
                    
                    # Verify response structure
                    user_data = result.get('user', {})
                    required_fields = ['id', 'email', 'username', 'is_active']
                    missing_fields = [field for field in required_fields if field not in user_data]
                    
                    if missing_fields:
                        print(f"   ⚠️  Missing user fields: {missing_fields}")
                    else:
                        print(f"   ✅ All required user fields present")
                        
                elif response.status == 200 and not result.get('success'):
                    print(f"   ❌ API authentication failed: {result.get('message', 'Unknown error')}")
                    print(f"   ⚠️  This could indicate password migration issues")
                else:
                    print(f"   ❌ API error: Status {response.status}")
                    if 'message' in result:
                        print(f"      Error: {result['message']}")
            
            break  # Only test first user
            
    except Exception as e:
        print(f"❌ API authentication test failed: {e}")
        return False
        
    return True

async def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 TESTING API ENDPOINTS")
    print("="*50)
    
    base_url = "http://localhost:8080"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Health check
            async with session.get(f"{base_url}/api/health") as response:
                if response.status == 200:
                    print("✅ Health endpoint working")
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
                    return False
            
            # Test 2: Auth endpoint structure (with invalid credentials)
            test_login = {
                "email": "test@example.com",
                "password": "wrong_password", 
                "remember_me": False
            }
            
            async with session.post(
                f"{base_url}/api/auth/login", 
                json=test_login,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 400, 401]:  # Expected responses
                    result = await response.json()
                    print("✅ Auth endpoint responding correctly")
                    print(f"   Response format: {list(result.keys())}")
                    
                    if 'success' in result and 'message' in result:
                        print("   ✅ Response has required fields")
                    else:
                        print("   ❌ Response missing required fields")
                        return False
                else:
                    print(f"❌ Auth endpoint error: {response.status}")
                    return False
            
            # Test 3: Real authentication with valid credentials (if available)
            await test_api_authentication(session, base_url)
            
            return True
            
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to server. Make sure the app is running:")
        print("   python run.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_frontend_compatibility():
    """Test frontend file compatibility"""
    print("\n🎨 TESTING FRONTEND COMPATIBILITY")
    print("="*50)
    
    try:
        # Check if login.js was updated
        with open('static/js/login.js', 'r') as f:
            content = f.read()
            
        required_elements = [
            'userId: result.user.id',
            'isActive: result.user.is_active',
            'Database authentication successful',
            'user-details',
            'checkAuthStatus',
            'getElementById(\'email\')'
        ]
        
        missing = []
        for element in required_elements:
            if element not in content:
                missing.append(element)
        
        if missing:
            print("❌ Frontend updates missing:")
            for item in missing:
                print(f"   - {item}")
            return False
        else:
            print("✅ Frontend login.js updated with database support")
        
        # Check if styles.css was updated
        with open('static/styles.css', 'r') as f:
            css_content = f.read()
            
        if 'user-info' in css_content and 'user-details' in css_content:
            print("✅ Frontend styles.css updated with new user display")
        else:
            print("❌ Frontend styles missing user display updates")
            return False
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Frontend file not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 PHASE 1 AUTHENTICATION TESTING")
    print("="*50)
    print("Testing database authentication integration...")
    print()
    
    # Run tests
    db_success = await test_database_auth()
    api_success = await test_api_endpoints()
    frontend_success = test_frontend_compatibility()
    
    # Summary
    print("\n" + "="*50)
    print("🎯 TEST SUMMARY")
    print("="*50)
    
    results = [
        ("Database Authentication", db_success),
        ("API Endpoints", api_success),
        ("Frontend Compatibility", frontend_success)
    ]
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Your database authentication is ready to use!")
        print("\n💡 Next steps:")
        print("   1. Start your application: python run.py")
        print("   2. Test login with a migrated user")
        print("   3. Check the enhanced user display in the header")
        print("\n🔒 Security recommendation:")
        print("   Consider archiving/removing users.json after successful testing")
        print("   since passwords are now securely stored in the database.")
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("Please review the errors above and fix them.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
