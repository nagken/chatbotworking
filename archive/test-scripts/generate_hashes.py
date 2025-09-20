from app.auth.password_utils import hash_password

passwords = {
    "admin123": "admin@pss-knowledge-assist.com",
    "test1234": "test@pss-knowledge-assist.com", 
    "demo1234": "demo@pss-knowledge-assist.com"
}

print("Generating password hashes...")
for pwd, email in passwords.items():
    try:
        hashed = hash_password(pwd)
        print(f"Email: {email}")
        print(f"Password: {pwd}")
        print(f"Hash: {hashed}")
        print("-" * 50)
    except Exception as e:
        print(f"Error hashing {pwd}: {e}")
