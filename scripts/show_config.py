#!/usr/bin/env python3
"""
Configuration Information Display Tool
Shows current configuration sources and database settings
"""

import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config

def main():
    """Display current configuration information"""
    
    print("🔧 CA Rebates Tool - Configuration Information")
    print("=" * 60)
    
    # Get comprehensive config info
    config_info = config.get_config_info()
    
    # Environment Information
    print(f"\n📍 Current Environment: {config_info['environment'].upper()}")
    
    # Configuration Sources
    print(f"\n📁 Configuration Sources:")
    sources = config_info['config_sources']
    
    for source, status in sources.items():
        icon = "✅" if status not in ["Not found"] else "❌"
        source_name = source.replace('_', ' ').title()
        print(f"   {icon} {source_name}: {status}")
    
    # Database Configuration
    print(f"\n🗄️  Database Configuration:")
    db_config = config_info['database_config']
    
    print(f"   Database Name: {db_config['database_name']}")
    print(f"   Host: {db_config['host']}")
    print(f"   Port: {db_config['port']}")
    print(f"   Connection URL: {db_config['database_url_preview']}")
    
    # Environment Variable Information
    print(f"\n🌍 Key Environment Variables:")
    key_vars = [
        'APP_ENVIRONMENT',
        'DB_HOST', 
        'DB_PORT',
        'DB_USER',
        'DB_PASSWORD',
        'PROD_DB_NAME',
        'TEST_DB_NAME', 
        'DEV_DB_NAME'
    ]
    
    for var in key_vars:
        value = os.getenv(var)
        if value:
            # Hide password for security
            if 'PASSWORD' in var:
                display_value = '***' 
            else:
                display_value = value
            print(f"   ✅ {var}={display_value}")
        else:
            print(f"   ❌ {var}=<not set>")
    
    # Instructions
    print(f"\n📋 Configuration Instructions:")
    print(f"   1. Create .env file for local development")
    print(f"   2. Use .env.test for testing environment")
    print(f"   3. Use system environment variables in production")
    print(f"   4. Copy .env.example as a starting template")
    
    print(f"\n💡 To switch environments:")
    print(f"   export APP_ENVIRONMENT=test")
    print(f"   export APP_ENVIRONMENT=development") 
    print(f"   export APP_ENVIRONMENT=production")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error displaying configuration: {e}")
        sys.exit(1)
