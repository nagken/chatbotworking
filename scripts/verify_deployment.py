#!/usr/bin/env python3
"""
PSS Knowledge Assist Deployment Verification Script
Checks that all components are working correctly
"""

import asyncio
import httpx
import os
import sys
import time
from pathlib import Path

# Add the app directory to the Python path
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_database_connection():
    """Check database connectivity"""
    try:
        from app.database.connection import get_async_engine
        from app.config import config
        
        engine = get_async_engine()
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            assert result.scalar() == 1
            
        logger.info("✅ Database connection successful")
        logger.info(f"   Database: {config.database_name}")
        logger.info(f"   Host: {config.DB_HOST}:{config.DB_PORT}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def check_application_health(base_url="http://localhost:8080"):
    """Check application health endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/health")
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ Application health check passed")
                logger.info(f"   Status: {health_data.get('status', 'unknown')}")
                logger.info(f"   Version: {health_data.get('version', 'unknown')}")
                return True
            else:
                logger.error(f"❌ Health check failed with status: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Application health check failed: {e}")
        return False


async def check_login_endpoint(base_url="http://localhost:8080"):
    """Check login functionality"""
    try:
        async with httpx.AsyncClient() as client:
            # Test login endpoint exists
            response = await client.post(
                f"{base_url}/api/auth/login",
                json={"email": "invalid@test.com", "password": "invalid"}
            )
            
            # Should return 401 for invalid credentials (but endpoint works)
            if response.status_code in [401, 422]:
                logger.info("✅ Login endpoint is accessible")
                return True
            else:
                logger.warning(f"⚠️ Login endpoint returned unexpected status: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Login endpoint check failed: {e}")
        return False


async def check_static_files(base_url="http://localhost:8080"):
    """Check static file serving"""
    try:
        async with httpx.AsyncClient() as client:
            # Check main page
            response = await client.get(f"{base_url}/")
            
            if response.status_code == 200 and "PSS Knowledge Assist" in response.text:
                logger.info("✅ Static files and main page served correctly")
                return True
            else:
                logger.error(f"❌ Static files check failed. Status: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Static files check failed: {e}")
        return False


async def main():
    """Main verification function"""
    
    logger.info("🔍 PSS Knowledge Assist Deployment Verification")
    logger.info("=" * 50)
    
    # Check if we're running in Kubernetes
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        base_url = "http://localhost:8080"  # Assumes port-forward
        logger.info("🔧 Kubernetes environment detected")
    else:
        base_url = "http://localhost:8080"
        logger.info("🔧 Local environment detected")
    
    logger.info(f"🌐 Testing against: {base_url}")
    logger.info("-" * 50)
    
    checks = []
    
    # Database check
    logger.info("1️⃣ Checking database connection...")
    db_ok = await check_database_connection()
    checks.append(("Database", db_ok))
    
    # Wait a moment for application to be ready
    logger.info("\n2️⃣ Checking application health...")
    app_ok = await check_application_health(base_url)
    checks.append(("Application Health", app_ok))
    
    # Login endpoint check
    logger.info("\n3️⃣ Checking authentication endpoints...")
    login_ok = await check_login_endpoint(base_url)
    checks.append(("Authentication", login_ok))
    
    # Static files check
    logger.info("\n4️⃣ Checking static file serving...")
    static_ok = await check_static_files(base_url)
    checks.append(("Static Files", static_ok))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 VERIFICATION SUMMARY")
    logger.info("=" * 50)
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{check_name:20} {status}")
        if not passed:
            all_passed = False
    
    logger.info("-" * 50)
    
    if all_passed:
        logger.info("🎉 All checks passed! PSS Knowledge Assist is ready to use.")
        logger.info(f"🌐 Access the application at: {base_url}")
        logger.info("👤 Default login credentials:")
        logger.info("   Admin: admin@pss-knowledge-assist.com / admin123")
        logger.info("   Test:  test@pss-knowledge-assist.com / test123")
        logger.info("⚠️  Remember to change default passwords!")
        return True
    else:
        logger.error("❌ Some checks failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
