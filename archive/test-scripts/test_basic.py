#!/usr/bin/env python3
"""
Simple test script for PSS Knowledge Assist
Tests basic functionality without requiring full database setup
"""

import sys
import os
from pathlib import Path

# Add app to path
app_root = Path(__file__).parent
sys.path.insert(0, str(app_root))

def test_imports():
    """Test if we can import the main components"""
    try:
        from app.config import config
        print("✅ Config import successful")
        print(f"   App Name: {config.APP_NAME}")
        print(f"   Environment: {config.APP_ENVIRONMENT}")
        print(f"   Port: {config.PORT}")
        return True
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False

def test_static_files():
    """Test if static files exist"""
    try:
        index_path = app_root / "static" / "index.html"
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "PSS Knowledge Assist" in content:
                    print("✅ Static files updated correctly")
                    return True
                else:
                    print("❌ Static files not updated")
                    return False
        else:
            print("❌ index.html not found")
            return False
    except Exception as e:
        print(f"❌ Static files test failed: {e}")
        return False

def test_system_prompt():
    """Test if PSS system prompt exists"""
    try:
        prompt_path = app_root / "app" / "system_prompts" / "pss_knowledge_assist_prompt.md"
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "PSS Knowledge Assist" in content and "Patient Support Services" in content:
                    print("✅ PSS system prompt exists and is correct")
                    return True
                else:
                    print("❌ PSS system prompt content incorrect")
                    return False
        else:
            print("❌ PSS system prompt not found")
            return False
    except Exception as e:
        print(f"❌ System prompt test failed: {e}")
        return False

def test_database_models():
    """Test if database models can be imported"""
    try:
        from app.database.models import User, ChatConversation, ChatMessage
        print("✅ Database models import successful")
        return True
    except Exception as e:
        print(f"❌ Database models import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 PSS Knowledge Assist - Basic Testing")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_imports),
        ("Static Files", test_static_files),
        ("System Prompt", test_system_prompt),
        ("Database Models", test_database_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! The application structure is correct.")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up PostgreSQL database")
        print("3. Run database setup: python scripts/setup_pss_database.py")
        print("4. Start application: python -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
