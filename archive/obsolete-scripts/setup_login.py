#!/usr/bin/env python3
"""
PSS Knowledge Assist - User Management Script
Creates/updates users with correct passwords for testing
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
app_root = Path(__file__).parent
sys.path.insert(0, str(app_root))

from app.auth.password_utils import hash_password, verify_password

def test_password_functions():
    """Test password hashing and verification"""
    print("🔐 Testing Password Functions")
    print("=" * 40)
    
    # Test password
    test_password = "admin123"
    
    # Hash the password
    hashed = hash_password(test_password)
    print(f"✅ Password hashed successfully")
    print(f"   Original: {test_password}")
    print(f"   Hashed: {hashed[:50]}...")
    
    # Verify the password
    is_valid = verify_password(test_password, hashed)
    print(f"✅ Password verification: {'PASS' if is_valid else 'FAIL'}")
    
    # Test wrong password
    wrong_password = "wrongpassword"
    is_invalid = verify_password(wrong_password, hashed)
    print(f"✅ Wrong password rejection: {'PASS' if not is_invalid else 'FAIL'}")
    
    return True

async def create_test_users():
    """Create test users with correct passwords"""
    try:
        from app.database.connection import init_database, get_async_engine
        from app.auth.user_repository import UserRepository
        from app.database.models import User
        from sqlalchemy.ext.asyncio import AsyncSession
        
        print("\n🔧 Setting up test users...")
        print("=" * 40)
        
        # Initialize database
        await init_database()
        engine = get_async_engine()
        
        async with AsyncSession(engine) as session:
            user_repo = UserRepository(session)
            
            # Test users to create/update
            test_users = [
                {
                    "email": "admin@pss-knowledge-assist.com",
                    "username": "PSS Admin",
                    "password": "admin123"
                },
                {
                    "email": "test@pss-knowledge-assist.com", 
                    "username": "Test User",
                    "password": "test123"
                },
                {
                    "email": "demo@pss-knowledge-assist.com",
                    "username": "Demo User", 
                    "password": "demo123"
                }
            ]
            
            for user_data in test_users:
                existing_user = await user_repo.get_user_by_email(user_data["email"])
                
                if existing_user:
                    print(f"🔄 User {user_data['email']} already exists - updating password")
                    # Update password
                    existing_user.password_hash = hash_password(user_data["password"])
                    session.add(existing_user)
                else:
                    print(f"➕ Creating new user: {user_data['email']}")
                    new_user = User(
                        email=user_data["email"],
                        username=user_data["username"],
                        password_hash=hash_password(user_data["password"]),
                        is_active=True
                    )
                    session.add(new_user)
                
                # Test the password immediately
                test_hash = hash_password(user_data["password"])
                is_valid = verify_password(user_data["password"], test_hash)
                print(f"   ✅ Password test: {'PASS' if is_valid else 'FAIL'}")
            
            await session.commit()
            print("✅ All users created/updated successfully!")
            
            return True
            
    except Exception as e:
        print(f"❌ Error setting up users: {e}")
        return False

def print_credentials():
    """Print the correct login credentials"""
    print("\n📋 PSS Knowledge Assist Login Credentials")
    print("=" * 50)
    print("🌐 Application URL: http://localhost:8080")
    print()
    print("👤 Available Login Accounts:")
    print("   Admin User:")
    print("     Email:    admin@pss-knowledge-assist.com")
    print("     Password: admin123")
    print()
    print("   Test User:")
    print("     Email:    test@pss-knowledge-assist.com")
    print("     Password: test123")
    print()
    print("   Demo User:")
    print("     Email:    demo@pss-knowledge-assist.com")
    print("     Password: demo123")
    print()
    print("⚠️  IMPORTANT: Change these passwords in production!")
    print("=" * 50)

async def main():
    """Main function"""
    print("🚀 PSS Knowledge Assist - User Setup")
    print("=" * 50)
    
    # Test password functions
    if not test_password_functions():
        print("❌ Password function tests failed!")
        return False
    
    # Try to create users (will skip if no database)
    try:
        await create_test_users()
    except Exception as e:
        print(f"⚠️  Database not available: {e}")
        print("   (This is normal if PostgreSQL isn't set up yet)")
    
    # Always print credentials
    print_credentials()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
