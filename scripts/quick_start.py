#!/usr/bin/env python3
"""
PSS Knowledge Assist Quick Start Script
Sets up the application for local development
"""

import subprocess
import sys
import os
import asyncio
from pathlib import Path

# Add the app directory to the Python path
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or app_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)


async def main():
    """Main setup function"""
    
    print("🚀 PSS Knowledge Assist Quick Start")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 11):
        logger.error("❌ Python 3.11+ is required")
        sys.exit(1)
    
    logger.info(f"✅ Python {python_version.major}.{python_version.minor} detected")
    
    # Check if .env file exists
    env_file = app_root / ".env"
    if not env_file.exists():
        logger.info("📄 Creating .env file from template...")
        example_env = app_root / ".env.example"
        if example_env.exists():
            with open(example_env, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            logger.info("✅ .env file created. Please update with your settings.")
        else:
            logger.warning("⚠️ .env.example not found. Please create .env manually.")
    
    # Install dependencies
    logger.info("📦 Installing Python dependencies...")
    success, output = run_command("pip install -r requirements.txt")
    if not success:
        logger.error(f"❌ Failed to install dependencies: {output}")
        sys.exit(1)
    
    logger.info("✅ Dependencies installed successfully")
    
    # Check if PostgreSQL is running
    logger.info("🗄️ Checking PostgreSQL connection...")
    try:
        from app.config import config
        import asyncpg
        
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database='postgres'  # Connect to default database first
        )
        await conn.close()
        logger.info("✅ PostgreSQL connection successful")
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        logger.error("Please ensure PostgreSQL is running and accessible.")
        logger.error("Update your .env file with correct database settings.")
        sys.exit(1)
    
    # Set up database
    logger.info("🔧 Setting up PSS Knowledge Assist database...")
    success, output = run_command("python scripts/setup_pss_database.py")
    if not success:
        logger.error(f"❌ Database setup failed: {output}")
        sys.exit(1)
    
    logger.info("✅ Database setup completed")
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 PSS Knowledge Assist is ready!")
    print("=" * 50)
    print("To start the application:")
    print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload")
    print("")
    print("Then visit: http://localhost:8080")
    print("")
    print("Default login credentials:")
    print("  Admin: admin@pss-knowledge-assist.com / admin123")
    print("  Test:  test@pss-knowledge-assist.com / test123")
    print("")
    print("⚠️  Remember to change these passwords!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
