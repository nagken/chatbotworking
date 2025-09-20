#!/usr/bin/env python3
"""
Test script to verify the CVS Pharmacy Knowledge Assist server can start properly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test FastAPI
        import fastapi
        print("✓ FastAPI imported successfully")
        
        # Test uvicorn
        import uvicorn
        print("✓ Uvicorn imported successfully")
        
        # Test our app modules
        from app.main import app
        print("✓ App main module imported successfully")
        
        from app.services.pdf_indexing_service import get_pdf_indexing_service
        print("✓ PDF indexing service imported successfully")
        
        from app.services.llm_service import LLMService
        print("✓ LLM service imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_pdf_service():
    """Test PDF indexing service initialization"""
    try:
        print("\nTesting PDF service...")
        pdf_service = get_pdf_indexing_service()
        
        # Check if GyaniNuxeo folder exists
        if os.path.exists("GyaniNuxeo"):
            print("✓ GyaniNuxeo folder found")
            pdf_files = [f for f in os.listdir("GyaniNuxeo") if f.endswith('.pdf') or f.endswith('.docx')]
            print(f"✓ Found {len(pdf_files)} document files")
        else:
            print("! GyaniNuxeo folder not found")
            
        return True
        
    except Exception as e:
        print(f"✗ PDF service test failed: {e}")
        return False

def test_static_files():
    """Test if static files exist"""
    try:
        print("\nTesting static files...")
        
        static_files = [
            "static/index.html",
            "static/styles.css", 
            "static/js/script.js",
            "static/js/conversation-manager.js"
        ]
        
        for file_path in static_files:
            if os.path.exists(file_path):
                print(f"✓ {file_path} exists")
            else:
                print(f"✗ {file_path} missing")
        
        return True
        
    except Exception as e:
        print(f"✗ Static files test failed: {e}")
        return False

if __name__ == "__main__":
    print("CVS Pharmacy Knowledge Assist - Server Test\n")
    
    success = True
    success &= test_imports()
    success &= test_pdf_service()
    success &= test_static_files()
    
    if success:
        print("\n✓ All tests passed! Server should start successfully.")
        print("\nTo start the server manually, run:")
        print('python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload')
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)
