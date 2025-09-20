from app.auth.password_utils import hash_password, verify_password

# Test password
password = "admin123"
print(f"Testing password: '{password}' (length: {len(password)})")

try:
    hashed = hash_password(password)
    print(f"✅ Password hashed successfully")
    
    # Test verification
    valid = verify_password(password, hashed)
    print(f"✅ Password verification: {valid}")
    
except Exception as e:
    print(f"❌ Error: {e}")
