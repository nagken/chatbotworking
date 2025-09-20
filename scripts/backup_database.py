#!/usr/bin/env python3
"""
Database Backup Script for CA Rebates Tool
Automated PostgreSQL database backups with environment awareness
"""

import asyncio
import sys
import subprocess
import os
import datetime
from pathlib import Path
import logging
from typing import Optional

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_backup_directory() -> Path:
    """Create and return backup directory path"""
    backup_dir = project_root / "backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def generate_backup_filename(environment: str, backup_type: str = "full") -> str:
    """Generate timestamped backup filename"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = config.database_name
    return f"{environment}_{db_name}_{backup_type}_{timestamp}"


def run_pg_dump(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    output_file: Path,
    backup_format: str = "custom"
) -> tuple[bool, str]:
    """Run pg_dump with specified parameters"""
    
    try:
        # Set password in environment for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h", host,
            "-p", str(port),
            "-U", user,
            "-d", database,
            "--no-password",  # Use PGPASSWORD instead of prompting
            "-v"  # Verbose output
        ]
        
        if backup_format == "custom":
            cmd.extend(["-Fc", "-f", str(output_file)])
        elif backup_format == "sql":
            cmd.extend(["-f", str(output_file)])
        elif backup_format == "sql_gzip":
            # For gzipped SQL, we'll pipe to gzip
            cmd.remove("-f")
            cmd.remove(str(output_file))
        
        logger.info(f"Running backup command: {' '.join(cmd[:8])}... (password hidden)")
        
        if backup_format == "sql_gzip":
            # Pipe pg_dump output to gzip
            with open(output_file, 'wb') as f:
                p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                p2 = subprocess.Popen(["gzip"], stdin=p1.stdout, stdout=f, stderr=subprocess.PIPE)
                p1.stdout.close()
                
                _, stderr = p2.communicate()
                p1.wait()
                
                if p1.returncode != 0 or p2.returncode != 0:
                    return False, f"Backup failed: {stderr.decode()}"
        else:
            # Direct pg_dump
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
            
            if result.returncode != 0:
                return False, f"Backup failed: {result.stderr}"
        
        # Check if backup file was created and has content
        if not output_file.exists() or output_file.stat().st_size == 0:
            return False, "Backup file was not created or is empty"
        
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        return True, f"Backup successful. File size: {file_size_mb:.2f} MB"
        
    except subprocess.TimeoutExpired:
        return False, "Backup timed out after 5 minutes"
    except FileNotFoundError:
        return False, "pg_dump command not found. Please install PostgreSQL client tools."
    except Exception as e:
        return False, f"Backup failed with error: {str(e)}"


def cleanup_old_backups(backup_dir: Path, keep_days: int = 7):
    """Remove backup files older than specified days"""
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        removed_count = 0
        
        for backup_file in backup_dir.glob("*.dump"):
            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                backup_file.unlink()
                removed_count += 1
                logger.info(f"Removed old backup: {backup_file.name}")
        
        for backup_file in backup_dir.glob("*.sql*"):
            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                backup_file.unlink()
                removed_count += 1
                logger.info(f"Removed old backup: {backup_file.name}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old backup files")
        else:
            logger.info("No old backup files to clean up")
            
    except Exception as e:
        logger.warning(f"Failed to cleanup old backups: {e}")


def backup_database(backup_format: str = "custom", cleanup_days: Optional[int] = None) -> bool:
    """Perform database backup"""
    
    # Get database configuration
    db_info = config.get_database_info()
    environment = db_info['environment']
    
    logger.info("🗄️  Starting database backup...")
    logger.info(f"Environment: {environment}")
    logger.info(f"Database: {db_info['database_name']}")
    logger.info(f"Host: {db_info['host']}")
    
    # Create backup directory
    backup_dir = create_backup_directory()
    
    # Generate backup filename
    base_filename = generate_backup_filename(environment)
    
    if backup_format == "custom":
        output_file = backup_dir / f"{base_filename}.dump"
    elif backup_format == "sql":
        output_file = backup_dir / f"{base_filename}.sql"
    elif backup_format == "sql_gzip":
        output_file = backup_dir / f"{base_filename}.sql.gz"
    else:
        logger.error(f"Unknown backup format: {backup_format}")
        return False
    
    # Perform backup
    success, message = run_pg_dump(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.database_name,
        output_file=output_file,
        backup_format=backup_format
    )
    
    if success:
        logger.info(f"✅ {message}")
        logger.info(f"Backup saved to: {output_file}")
        
        # Cleanup old backups if requested
        if cleanup_days is not None:
            cleanup_old_backups(backup_dir, cleanup_days)
        
        return True
    else:
        logger.error(f"❌ {message}")
        # Remove partial backup file if it exists
        if output_file.exists():
            output_file.unlink()
        return False


async def main():
    """Main backup function"""
    
    print("🗄️  CA Rebates Tool - Database Backup Utility")
    print("=" * 50)
    
    # Handle command line arguments
    if len(sys.argv) < 2:
        print("""
Available commands:
  custom     - Custom format backup (recommended, allows selective restore)
  sql        - Plain SQL backup (human readable, larger size)
  sql_gzip   - Compressed SQL backup (smaller size)
  cleanup    - Cleanup old backups (keeps last 7 days)

Options:
  --cleanup-days N  - Remove backups older than N days (default: no cleanup)

Examples:
  python scripts/backup_database.py custom
  python scripts/backup_database.py sql --cleanup-days 7
  python scripts/backup_database.py sql_gzip --cleanup-days 30
        """)
        return 0
    
    backup_format = sys.argv[1].lower()
    cleanup_days = None
    
    # Parse cleanup days option
    if "--cleanup-days" in sys.argv:
        try:
            cleanup_index = sys.argv.index("--cleanup-days")
            cleanup_days = int(sys.argv[cleanup_index + 1])
        except (IndexError, ValueError):
            print("❌ Invalid --cleanup-days value. Must be a number.")
            return 1
    
    # Validate backup format
    valid_formats = ["custom", "sql", "sql_gzip", "cleanup"]
    if backup_format not in valid_formats:
        print(f"❌ Invalid backup format: {backup_format}")
        print(f"Valid formats: {', '.join(valid_formats)}")
        return 1
    
    try:
        if backup_format == "cleanup":
            # Just cleanup old backups
            backup_dir = create_backup_directory()
            days = cleanup_days or 7
            logger.info(f"Cleaning up backups older than {days} days...")
            cleanup_old_backups(backup_dir, days)
            print("✅ Cleanup completed")
            return 0
        else:
            # Perform backup
            success = backup_database(backup_format, cleanup_days)
            return 0 if success else 1
            
    except KeyboardInterrupt:
        print("\n👋 Backup cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
