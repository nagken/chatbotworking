#!/usr/bin/env python3
"""
Setup script for creating and initializing test/development databases
Run this script to safely create test databases without affecting production
"""

import os
import asyncio
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
import logging
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config
from app.database.models import Base

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_database_if_not_exists(database_name: str):
    """Create database if it doesn't exist"""
    
    # Connect to postgres database to create new databases
    admin_url = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/postgres"
    
    engine = create_engine(admin_url)
    
    try:
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :db_name"), {"db_name": database_name})
            
            if result.fetchone():
                logger.info(f"✅ Database '{database_name}' already exists")
                return True
            
            # Create database
            conn.execute(text("COMMIT"))  # End any transaction
            conn.execute(text(f"CREATE DATABASE {database_name}"))
            logger.info(f"✅ Created database '{database_name}'")
            return True
            
    except ProgrammingError as e:
        logger.error(f"❌ Failed to create database '{database_name}': {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error creating database '{database_name}': {e}")
        return False
    finally:
        engine.dispose()


async def create_tables(database_name: str):
    """Create tables in the specified database"""
    try:
        from app.database.connection import init_database, get_db_session, close_database
        
        # Initialize database connection (will use current APP_ENVIRONMENT setting)
        await init_database()
        
        # Use session context manager for consistency
        async with get_db_session() as session:
            # Create all tables using the session
            async with session.begin():
                await session.run_sync(Base.metadata.create_all)
        
        logger.info(f"✅ Created tables in database '{database_name}'")
        
        # Cleanup - close database connections
        await close_database()
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables in '{database_name}': {e}")
        return False


def show_database_config():
    """Show current database configuration"""
    config_info = config.get_config_info()
    
    print("\n" + "="*50)
    print("CONFIGURATION INFORMATION")
    print("="*50)
    print(f"Environment: {config_info['environment']}")
    print(f"Database Name: {config_info['database_config']['database_name']}")
    print(f"Host: {config_info['database_config']['host']}")
    print(f"Port: {config_info['database_config']['port']}")
    print(f"Connection URL: {config_info['database_config']['database_url_preview']}")
    
    print("\nConfig Sources:")
    sources = config_info['config_sources']
    print(f"  Base .env file: {sources['base_env_file']}")
    print(f"  Environment-specific file: {sources['environment_specific_file']}")
    print(f"  System environment variables: {sources['system_env_vars']}")
    print("="*50 + "\n")


async def main():
    """Main setup function"""
    
    print("🚀 CA Rebates Tool - Database Setup")
    print("This script will help you create and initialize test databases safely\n")
    
    # Show current configuration
    show_database_config()
    
    # Determine what to create based on current environment
    current_db = config.database_name
    
    if config.APP_ENVIRONMENT.lower() == 'production':
        print(f"⚠️  You're in PRODUCTION environment!")
        print(f"Current database: '{current_db}'")
        print("To create test databases, set APP_ENVIRONMENT=test or APP_ENVIRONMENT=development")
        print("\nExample:")
        print("export APP_ENVIRONMENT=test")
        print("python setup_test_db.py")
        return
    
    print(f"Creating database: '{current_db}'")
    
    # Step 1: Create database
    if not create_database_if_not_exists(current_db):
        print(f"❌ Failed to create database '{current_db}'")
        return
    
    # Step 2: Create tables
    if not await create_tables(current_db):
        print(f"❌ Failed to create tables in '{current_db}'")
        return
    
    print(f"\n🎉 Successfully set up database '{current_db}'!")
    
    # Show instructions
    print("\n📋 Next Steps:")
    print(f"1. Your app is now configured to use: '{current_db}'")
    print("2. You can now run your application safely")
    print("3. To switch between databases, change APP_ENVIRONMENT:")
    print("   - export APP_ENVIRONMENT=production  # Uses 'mydatabase'")
    print("   - export APP_ENVIRONMENT=test        # Uses 'ca_rebates_test'")
    print("   - export APP_ENVIRONMENT=development # Uses 'ca_rebates_dev'")
    print("\n4. Create test users with:")
    print("   python scripts/bulk_create_users.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)
