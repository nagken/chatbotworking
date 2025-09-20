#!/usr/bin/env python3
"""
Debug script to check what routes are actually registered in the app
"""
import os
import sys

# Change to project directory and add to path
os.chdir(r'c:\cvssep9')
sys.path.insert(0, os.getcwd())

try:
    print("Importing the main app...")
    from app.main import app
    
    print(f"✅ App imported successfully")
    print(f"✅ App title: {app.title}")
    print(f"✅ Total routes: {len(app.routes)}")
    
    print("\n🔍 All registered routes:")
    for i, route in enumerate(app.routes, 1):
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"   {i:2d}. {list(route.methods)} {route.path}")
        else:
            print(f"   {i:2d}. {type(route).__name__} {getattr(route, 'path', 'N/A')}")
    
    print("\n🎯 Looking specifically for test-login routes:")
    test_login_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and 'test-login' in route.path:
            test_login_routes.append(route)
            print(f"   ✅ Found: {list(route.methods)} {route.path}")
    
    if not test_login_routes:
        print("   ❌ No test-login routes found!")
        
        print("\n🔍 Routes that might be similar:")
        for route in app.routes:
            if hasattr(route, 'path'):
                path = route.path.lower()
                if 'test' in path or 'login' in path:
                    print(f"   - {list(route.methods)} {route.path}")
    
    print(f"\n📊 Route summary:")
    print(f"   - Total routes: {len(app.routes)}")
    print(f"   - Test-login routes: {len(test_login_routes)}")
    
    # Check if the route function exists
    print(f"\n🔧 Checking route function...")
    for route in app.routes:
        if hasattr(route, 'path') and route.path == '/test-login':
            print(f"   ✅ Route function: {route.endpoint}")
            break
    else:
        print(f"   ❌ No /test-login route function found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
