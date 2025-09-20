#!/usr/bin/env python3
"""
Test script to demonstrate environment variable loading priority
"""

import os
from dotenv import load_dotenv

def show_env_before_loading():
    print("🔍 BEFORE loading .env files:")
    print(f"   APP_ENVIRONMENT: {os.getenv('APP_ENVIRONMENT', 'NOT SET')}")
    print(f"   DB_PASSWORD: {os.getenv('DB_PASSWORD', 'NOT SET')}")
    print(f"   SECRET_KEY: {os.getenv('SECRET_KEY', 'NOT SET')}")
    print()

def show_env_after_loading():
    print("🔍 AFTER loading .env files:")
    print(f"   APP_ENVIRONMENT: {os.getenv('APP_ENVIRONMENT', 'NOT SET')}")
    print(f"   DB_PASSWORD: {os.getenv('DB_PASSWORD', 'NOT SET')}")
    print(f"   SECRET_KEY: {os.getenv('SECRET_KEY', 'NOT SET')}")
    print()

def main():
    print("🧪 Environment Variable Loading Test")
    print("=" * 50)
    
    # Show what's available from system environment
    show_env_before_loading()
    
    # Load .env file
    print("📝 Loading .env file...")
    load_dotenv()
    show_env_after_loading()
    
    # Show what files exist
    print("📁 Available .env files:")
    env_files = ['.env', '.env.development', '.env.test', '.env.production']
    for file in env_files:
        status = "✅ EXISTS" if os.path.exists(file) else "❌ NOT FOUND"
        print(f"   {file}: {status}")
    
    print("\n" + "=" * 50)
    print("💡 Key Points:")
    print("   • System environment variables have highest priority")
    print("   • load_dotenv() won't override system variables")
    print("   • load_dotenv(file, override=True) CAN override")
    print("   • Files are loaded in order: .env, then .env.{environment}")

if __name__ == "__main__":
    main()
