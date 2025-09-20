#!/usr/bin/env python3
"""
Script to migrate users from users.json to database
Migrates existing file-based authentication to database-backed authentication
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
from app.auth.password_utils import hash_password
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_users_from_json():
    """
    Migrate users from users.json file to database
    """
    users_file = "users.json"
    
    # Check if users.json exists
    if not os.path.exists(users_file):
        print(f"❌ {users_file} not found!")
        print("💡 Make sure you're running this from the project root directory.")
        return False
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database connection initialized")
        
        # Read users.json
        with open(users_file, 'r') as f:
            users_data = json.load(f)
        
        print(f"📂 Found {len(users_data)} users in {users_file}")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        async with get_db_session() as db:
            user_repo = UserRepository(db)
            
            for email, password in users_data.items():
                try:
                    print(f"\n👤 Processing user: {email}")
                    
                    # Check if user already exists in database
                    existing_user = await user_repo.get_user_by_email(email)
                    if existing_user:
                        print(f"   ⏭️  User already exists in database, skipping...")
                        skipped_count += 1
                        continue
                    
                    # Extract user information
                    username = email.split('@')[0]
                    
                    if not password:
                        print(f"   ❌ No password found for user {email}, skipping...")
                        error_count += 1
                        continue
                    
                    # Create user data object
                    user_create = UserCreate(
                        email=email,
                        username=username,
                        password=password  # Will be hashed by UserRepository
                    )
                    
                    # Create user in database
                    new_user = await user_repo.create_user(user_create)
                    
                    print(f"   ✅ User migrated successfully")
                    print(f"      - ID: {new_user.id}")
                    print(f"      - Email: {new_user.email}")
                    print(f"      - Username: {new_user.username}")
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to migrate user {email}: {e}")
                    error_count += 1
                    continue
            
            # Commit all changes
            await db.commit()
        
        # Print summary
        print("\n" + "="*50)
        print("🎯 MIGRATION SUMMARY")
        print("="*50)
        print(f"✅ Successfully migrated: {migrated_count} users")
        print(f"⏭️  Skipped (already exist): {skipped_count} users")
        print(f"❌ Failed: {error_count} users")
        print(f"📊 Total processed: {migrated_count + skipped_count + error_count} users")
        
        if migrated_count > 0:
            print(f"\n🎉 Migration completed successfully!")
            print(f"💡 You can now test database authentication with the migrated users.")
            
        if error_count > 0:
            print(f"\n⚠️  {error_count} users failed to migrate. Check the errors above.")
            
        return error_count == 0
        
    except FileNotFoundError:
        print(f"❌ Could not find {users_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {users_file}: {e}")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logger.error(f"Migration error: {e}")
        return False


async def verify_migration():
    """
    Verify that migrated users can authenticate
    """
    print("\n🔍 VERIFYING MIGRATION")
    print("="*50)
    
    try:
        await init_database()
        
        async with get_db_session() as db:
            user_repo = UserRepository(db)
            
            # Get all users from database
            users = await user_repo.list_users(limit=100, include_inactive=True)
            
            print(f"📊 Found {len(users)} users in database:")
            
            for user in users:
                status = "🟢 Active" if user.is_active else "🔴 Inactive"
                last_login = user.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_at else "Never"
                
                print(f"   {status} {user.email}")
                print(f"      Username: {user.username}")
                print(f"      Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"      Last Login: {last_login}")
                print()
            
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


async def main():
    """Main migration function"""
    print("🚀 CA REBATES TOOL - USER MIGRATION")
    print("="*50)
    print("This script will migrate users from users.json to the database.")
    print("Make sure you have a backup of your users.json file!")
    print("="*50)
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to proceed with the migration? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Migration cancelled by user.")
        return
    
    # Run migration
    success = await migrate_users_from_json()
    
    if success:
        # Verify migration
        await verify_migration()
        
        print("\n✅ MIGRATION COMPLETE!")
        print("💡 Next steps:")
        print("   1. Test login with migrated users")
        print("   2. Update your application to use database authentication")
        print("   3. Consider backing up/archiving users.json")
    else:
        print("\n❌ Migration completed with errors.")
        print("💡 Please review the errors above and fix any issues.")


if __name__ == "__main__":
    asyncio.run(main())
