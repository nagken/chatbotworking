#!/usr/bin/env python3
"""
Database connection test script for CA Rebates Tool
Tests connectivity to PostgreSQL databases across different environments
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.connection import init_database, test_connection, get_database_info, health_check, close_database
from app.config import config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """Test database connection and display connection info"""
    
    print("=" * 60)
    print("CA Rebates Tool - Database Connection Test")
    print("=" * 60)
    print()
    
    # Display configuration
    print(f"🔧 Configuration:")
    db_info = config.get_database_info()
    print(f"   Environment: {db_info['environment']}")
    print(f"   Host: {db_info['host']}")
    print(f"   Port: {db_info['port']}")
    print(f"   Database: {db_info['database_name']}")
    print(f"   User: {config.DB_USER}")
    print(f"   Pool Size: {config.DB_POOL_SIZE}")
    print(f"   Max Overflow: {config.DB_MAX_OVERFLOW}")
    print(f"   Pool Timeout: {config.DB_POOL_TIMEOUT}s")
    print(f"   Pool Recycle: {config.DB_POOL_RECYCLE}s")
    print(f"   Pool Pre-ping: {config.DB_POOL_PRE_PING}")
    print(f"   SQL Echo: {config.DB_ECHO}")
    print()
    
    try:
        print("🚀 Initializing database connection...")
        await init_database()
        print("✅ Database initialization successful!")
        print()
        
        print("🧪 Testing database connectivity...")
        connection_test = await test_connection()
        if connection_test:
            print("✅ Database connection test successful!")
        else:
            print("❌ Database connection test failed!")
            return False
        print()
        
        print("📊 Getting database information...")
        db_info = await get_database_info()
        print(f"   Status: {db_info.get('status', 'unknown')}")
        if db_info.get('status') == 'connected':
            print(f"   Database: {db_info.get('database_name', 'N/A')}")
            print(f"   Version: {db_info.get('version', 'N/A')}")
            print(f"   Active Connections: {db_info.get('active_connections', 'N/A')}")
            print(f"   Pool Size: {db_info.get('pool_size', 'N/A')}")
            print(f"   Max Overflow: {db_info.get('max_overflow', 'N/A')}")
        elif db_info.get('error'):
            print(f"   Error: {db_info.get('error')}")
        print()
        
        print("🏥 Performing health check...")
        health = await health_check()
        if health.get('healthy'):
            print(f"✅ Database is healthy!")
            print(f"   Response Time: {health.get('response_time_ms', 'N/A')} ms")
        else:
            print(f"❌ Database health check failed!")
            if health.get('error'):
                print(f"   Error: {health.get('error')}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        logger.error(f"Database connection error: {e}", exc_info=True)
        return False
        
    finally:
        print("🔄 Closing database connections...")
        await close_database()
        print("✅ Database connections closed.")
        print()


async def test_specific_environment(environment: str):
    """Test a specific environment by setting APP_ENVIRONMENT"""
    
    # Temporarily override the environment
    original_env = config.APP_ENVIRONMENT
    config.APP_ENVIRONMENT = environment
    
    try:
        print(f"\n{'='*20} Testing {environment.title()} Environment {'='*20}")
        
        success = await test_database_connection()
        return success
        
    finally:
        # Restore original environment
        config.APP_ENVIRONMENT = original_env


async def main():
    """Main test function"""
    
    print("Starting database connection tests...\n")
    
    if len(sys.argv) > 1 and sys.argv[1] in ['test', 'development', 'production', 'all']:
        test_mode = sys.argv[1]
    else:
        test_mode = 'current'  # Test current configuration only
    
    success_count = 0
    total_tests = 0
    
    if test_mode == 'test':
        total_tests = 1
        if await test_specific_environment('test'):
            success_count += 1
            
    elif test_mode == 'development':
        total_tests = 1
        if await test_specific_environment('development'):
            success_count += 1
            
    elif test_mode == 'production':
        total_tests = 1
        if await test_specific_environment('production'):
            success_count += 1
            
    elif test_mode == 'all':
        total_tests = 3
        print("Testing all environments...")
        
        if await test_specific_environment('production'):
            success_count += 1
            
        if await test_specific_environment('test'):
            success_count += 1
            
        if await test_specific_environment('development'):
            success_count += 1
            
    else:  # test_mode == 'current'
        total_tests = 1
        if await test_database_connection():
            success_count += 1
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All database connection tests passed!")
        return 0
    else:
        print("⚠️  Some database connection tests failed.")
        return 1


if __name__ == "__main__":
    print("CA Rebates Tool - Database Connection Test Script")
    print("Usage:")
    print("  python scripts/test_db_connection.py              # Test current config")
    print("  python scripts/test_db_connection.py test         # Test test database")
    print("  python scripts/test_db_connection.py development  # Test development database")
    print("  python scripts/test_db_connection.py production   # Test production database")
    print("  python scripts/test_db_connection.py all          # Test all environments")
    print()
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
