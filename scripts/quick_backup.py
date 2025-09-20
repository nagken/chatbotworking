#!/usr/bin/env python3
"""
Quick Emergency Database Backup Script
For fast backups before running migrations or emergency situations
"""

import sys
import subprocess
import os
import datetime
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import config

def quick_backup():
    """Perform a quick emergency backup"""
    
    # Get database configuration
    db_info = config.get_database_info()
    
    print(f"🚨 EMERGENCY BACKUP - {db_info['environment'].upper()}")
    print("=" * 50)
    print(f"Database: {db_info['database_name']}")
    print(f"Host: {db_info['host']}")
    print()
    
    # Create backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    environment = db_info['environment']
    db_name = db_info['database_name']
    
    # Create backups directory
    backup_dir = project_root / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    backup_file = backup_dir / f"EMERGENCY_{environment}_{db_name}_{timestamp}.dump"
    
    # Set password in environment
    env = os.environ.copy()
    env['PGPASSWORD'] = config.DB_PASSWORD
    
    print(f"Creating backup: {backup_file.name}")
    print("This may take a few minutes for large databases...")
    print()
    
    try:
        # Run pg_dump
        cmd = [
            "pg_dump",
            "-h", config.DB_HOST,
            "-p", str(config.DB_PORT),
            "-U", config.DB_USER,
            "-d", config.database_name,
            "-Fc",  # Custom format
            "-f", str(backup_file),
            "--no-password",
            "-v"
        ]
        
        result = subprocess.run(cmd, env=env, timeout=600)  # 10 minute timeout
        
        if result.returncode == 0:
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"✅ BACKUP SUCCESSFUL!")
            print(f"📁 File: {backup_file}")
            print(f"📊 Size: {file_size_mb:.2f} MB")
            print()
            print("🔄 You can now safely proceed with your migrations.")
            print()
            print("To restore this backup if needed:")
            print(f"pg_restore -h HOST -p PORT -U USER -d DATABASE {backup_file}")
            return True
        else:
            print(f"❌ BACKUP FAILED!")
            print("Please check your database connection and try again.")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ BACKUP TIMED OUT!")
        print("Database may be too large or connection is slow.")
        return False
    except FileNotFoundError:
        print("❌ pg_dump not found!")
        print("Please install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"❌ BACKUP ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = quick_backup()
    sys.exit(0 if success else 1)
