#!/usr/bin/env python3
"""
Direct route test - test the route function directly
"""
import os
import sys
import asyncio

# Change to project directory and add to path
os.chdir(r'c:\cvssep9')
sys.path.insert(0, os.getcwd())

async def test_route_directly():
    """Test the route function directly"""
    try:
        print("Importing app...")
        from app.main import app
        
        print("✅ App imported successfully")
        
        # Find the test_login_page function
        for route in app.routes:
            if hasattr(route, 'path') and route.path == '/test-login':
                print(f"✅ Found test-login route: {route}")
                
                # Call the route function directly
                print("Calling route function...")
                response = await route.endpoint()
                print(f"✅ Route function executed successfully")
                print(f"✅ Response type: {type(response)}")
                
                # Check if it's HTMLResponse
                if hasattr(response, 'body'):
                    body = response.body
                    if isinstance(body, bytes):
                        body_str = body.decode('utf-8')
                    else:
                        body_str = str(body)
                    
                    if "PSS Knowledge Assist" in body_str:
                        print("✅ Response contains expected content")
                    else:
                        print("❌ Response doesn't contain expected content")
                        print(f"First 200 chars: {body_str[:200]}")
                else:
                    print(f"Response: {response}")
                
                return True
        
        print("❌ test-login route not found in app.routes")
        
        # Debug: show all routes
        print("\nAll routes:")
        for i, route in enumerate(app.routes):
            if hasattr(route, 'path'):
                print(f"  {i}: {route.path}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== Direct Route Test ===")
    result = asyncio.run(test_route_directly())
    
    if result:
        print("\n✅ Route test passed - the function works correctly")
        print("The issue might be with server startup or routing registration")
    else:
        print("\n❌ Route test failed - there's an issue with the route definition")

if __name__ == "__main__":
    main()
