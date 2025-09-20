#!/usr/bin/env python3
"""
Test authentication functionality
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.auth.password_utils import hash_password, verify_password

def test_password_verification():
    """Test password hashing and verification"""
    print("Testing password verification...")
    
    # Test password
    password = "admin123"
    
    # Hash it
    password_hash = hash_password(password)
    print(f"Password: {password}")
    print(f"Hash: {password_hash}")
    
    # Verify it
    is_valid = verify_password(password, password_hash)
    print(f"Verification result: {is_valid}")
    
    # Test wrong password
    wrong_password = "wrong123"
    is_wrong_valid = verify_password(wrong_password, password_hash)
    print(f"Wrong password verification: {is_wrong_valid}")
    
    return is_valid

def test_fallback_auth():
    """Test the fallback authentication"""
    print("\nTesting fallback authentication...")
    
    from app.api.routes.auth import get_temp_users
    temp_users = get_temp_users()
    
    admin_user = temp_users.get("admin@pss-knowledge-assist.com")
    if admin_user:
        print(f"Admin user found: {admin_user['email']}")
        print(f"Username: {admin_user['username']}")
        
        # Test password verification
        test_password = "admin123"
        is_valid = verify_password(test_password, admin_user['password_hash'])
        print(f"Password '{test_password}' verification: {is_valid}")
        
        return is_valid
    else:
        print("Admin user not found!")
        return False

if __name__ == "__main__":
    print("🔐 Testing PSS Knowledge Assist Authentication")
    print("=" * 50)
    
    # Test basic password functions
    basic_test = test_password_verification()
    
    # Test fallback auth
    fallback_test = test_fallback_auth()
    
    print("\n" + "=" * 50)
    if basic_test and fallback_test:
        print("✅ All authentication tests passed!")
    else:
        print("❌ Some authentication tests failed!")
        sys.exit(1)
