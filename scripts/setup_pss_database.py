#!/usr/bin/env python3
"""
PSS Knowledge Assist Database Setup Script
Creates initial database, runs migrations, and sets up initial data
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

from app.database.connection import init_database, get_async_engine
from app.config import config
from app.auth.user_repository import UserRepository
from app.auth.password_utils import hash_password
from app.database.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_initial_admin_user():
    """Create an initial admin user for PSS Knowledge Assist"""
    
    try:
        # Initialize database connection
        await init_database()
        
        # Get database session
        engine = get_async_engine()
        
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            user_repo = UserRepository(session)
            
            # Check if admin user already exists
            admin_email = "admin@pss-knowledge-assist.com"
            existing_user = await user_repo.get_user_by_email(admin_email)
            
            if existing_user:
                logger.info(f"Admin user {admin_email} already exists")
                return
            
            # Create admin user
            admin_user = User(
                email=admin_email,
                username="PSS Admin",
                password_hash=hash_password("admin123"),  # Change this password!
                is_active=True
            )
            
            created_user = await user_repo.create_user(admin_user)
            logger.info(f"Created admin user: {created_user.email}")
            
            # Create a test user
            test_email = "test@pss-knowledge-assist.com"
            existing_test = await user_repo.get_user_by_email(test_email)
            
            if not existing_test:
                test_user = User(
                    email=test_email,
                    username="Test User",
                    password_hash=hash_password("test123"),  # Change this password!
                    is_active=True
                )
                
                created_test = await user_repo.create_user(test_user)
                logger.info(f"Created test user: {created_test.email}")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error creating initial users: {e}")
        raise


async def main():
    """Main setup function"""
    
    logger.info("🚀 Setting up PSS Knowledge Assist Database")
    logger.info(f"Database: {config.database_name}")
    logger.info(f"Environment: {config.APP_ENVIRONMENT}")
    
    try:
        # Run database migrations first
        logger.info("📊 Running database migrations...")
        import subprocess
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=app_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Migration failed: {result.stderr}")
            return False
        
        logger.info("✅ Database migrations completed")
        
        # Create initial users
        logger.info("👤 Creating initial users...")
        await create_initial_admin_user()
        logger.info("✅ Initial users created")
        
        logger.info("🎉 Database setup completed successfully!")
        
        print("\n" + "="*50)
        print("PSS Knowledge Assist Database Setup Complete!")
        print("="*50)
        print(f"Environment: {config.APP_ENVIRONMENT}")
        print(f"Database: {config.database_name}")
        print("\nInitial Users Created:")
        print("  Admin: admin@pss-knowledge-assist.com / admin123")
        print("  Test:  test@pss-knowledge-assist.com / test123")
        print("\n⚠️  IMPORTANT: Change these default passwords!")
        print("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
