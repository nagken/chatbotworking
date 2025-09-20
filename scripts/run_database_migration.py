#!/usr/bin/env python3
"""
Database Migration Runner for CA Rebates Tool
Safely runs database schema migrations with proper checking and rollback options
"""

import asyncio
import sys
import subprocess
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.connection import init_database, test_connection, close_database
from app.config import config
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_alembic_command(command: str) -> tuple[bool, str]:
    """Run an alembic command and return success status and output"""
    try:
        # Change to project root directory
        original_dir = os.getcwd()
        os.chdir(project_root)
        
        # Run the alembic command
        result = subprocess.run(
            ["python", "-m", "alembic"] + command.split(),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Return to original directory
        os.chdir(original_dir)
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr or result.stdout
            
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 60 seconds"
    except Exception as e:
        return False, f"Command failed: {str(e)}"


async def check_database_connection():
    """Check if we can connect to the database"""
    try:
        logger.info("Checking database connection...")
        await init_database()
        
        if await test_connection():
            logger.info("✅ Database connection successful")
            return True
        else:
            logger.error("❌ Database connection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False
    finally:
        await close_database()


def show_current_migration_status():
    """Show current migration status"""
    logger.info("Checking current migration status...")
    
    success, output = run_alembic_command("current")
    if success:
        if output.strip():
            logger.info(f"✅ Current migration: {output.strip()}")
        else:
            logger.info("ℹ️  No migrations have been applied yet")
        return True
    else:
        logger.error(f"❌ Failed to check migration status: {output}")
        return False


def show_migration_history():
    """Show migration history"""
    logger.info("Showing migration history...")
    
    success, output = run_alembic_command("history --verbose")
    if success:
        print(f"\nMigration History:\n{output}")
        return True
    else:
        logger.error(f"❌ Failed to get migration history: {output}")
        return False


def run_migration_upgrade(target="head"):
    """Run migration upgrade"""
    logger.info(f"Running migration upgrade to {target}...")
    
    success, output = run_alembic_command(f"upgrade {target}")
    if success:
        logger.info("✅ Migration upgrade successful")
        if output.strip():
            print(f"\nMigration Output:\n{output}")
        return True
    else:
        logger.error(f"❌ Migration upgrade failed: {output}")
        return False


def run_migration_downgrade(target):
    """Run migration downgrade"""
    logger.info(f"Running migration downgrade to {target}...")
    
    success, output = run_alembic_command(f"downgrade {target}")
    if success:
        logger.info("✅ Migration downgrade successful")
        if output.strip():
            print(f"\nMigration Output:\n{output}")
        return True
    else:
        logger.error(f"❌ Migration downgrade failed: {output}")
        return False


def show_pending_migrations():
    """Show pending migrations that haven't been applied"""
    logger.info("Checking for pending migrations...")
    
    # First get current migration
    current_success, current_output = run_alembic_command("current")
    if not current_success:
        logger.error("❌ Failed to get current migration status")
        return False
    
    # Get all migrations
    history_success, history_output = run_alembic_command("history")
    if not history_success:
        logger.error("❌ Failed to get migration history")
        return False
    
    current_migration = current_output.strip()
    
    if not current_migration:
        logger.info("ℹ️  No migrations applied yet. All migrations are pending.")
        return True
    
    # Check if we're at the latest
    head_success, head_output = run_alembic_command("current")
    if head_success and "head" in head_output:
        logger.info("✅ Database is up to date with latest migrations")
    else:
        logger.info("⚠️  There may be pending migrations")
    
    return True


async def main():
    """Main migration runner"""
    
    print("🚀 CA Rebates Tool - Database Migration Runner")
    print("=" * 50)
    
    # Show configuration
    db_info = config.get_database_info()
    print(f"Environment: {db_info['environment']}")
    print(f"Database: {db_info['database_name']}")
    print(f"Host: {db_info['host']}")
    print("=" * 50)
    
    # Check database connection first
    if not await check_database_connection():
        print("❌ Cannot proceed without database connection")
        return 1
    
    # Handle command line arguments
    if len(sys.argv) < 2:
        print("""
Available commands:
  status     - Show current migration status
  history    - Show migration history
  pending    - Show pending migrations
  upgrade    - Run migration upgrade to head
  upgrade X  - Run migration upgrade to specific revision X
  downgrade X - Run migration downgrade to revision X
  test       - Run migration tests after upgrade

Examples:
  python scripts/run_database_migration.py status
  python scripts/run_database_migration.py upgrade
  python scripts/run_database_migration.py upgrade 001_initial_schema
  python scripts/run_database_migration.py downgrade 001_initial_schema
  python scripts/run_database_migration.py test
        """)
        return 0
    
    command = sys.argv[1].lower()
    
    try:
        if command == "status":
            success = show_current_migration_status()
            
        elif command == "history":
            success = show_migration_history()
            
        elif command == "pending":
            success = show_pending_migrations()
            
        elif command == "upgrade":
            target = sys.argv[2] if len(sys.argv) > 2 else "head"
            success = run_migration_upgrade(target)
            
        elif command == "downgrade":
            if len(sys.argv) < 3:
                print("❌ Downgrade requires a target revision")
                print("Example: python scripts/run_database_migration.py downgrade 001_initial_schema")
                return 1
            target = sys.argv[2]
            success = run_migration_downgrade(target)
            
        elif command == "test":
            # First upgrade to head
            if not run_migration_upgrade("head"):
                print("❌ Migration upgrade failed, cannot run tests")
                return 1
            
            # Then run schema verification
            print("\n" + "="*50)
            print("Running database schema verification...")
            print("="*50)
            
            test_process = subprocess.run([
                "python", "scripts/verify_migration_schema.py"
            ], cwd=project_root)
            
            success = test_process.returncode == 0
            
        else:
            print(f"❌ Unknown command: {command}")
            return 1
        
        if success:
            print(f"\n✅ Command '{command}' completed successfully")
            return 0
        else:
            print(f"\n❌ Command '{command}' failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
