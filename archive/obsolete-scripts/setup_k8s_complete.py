#!/usr/bin/env python3
"""
PSS Knowledge Assist - Complete Setup with Kubernetes PostgreSQL
"""

import asyncio
import sys
import subprocess
from pathlib import Path

# Add app to path
app_root = Path(__file__).parent
sys.path.insert(0, str(app_root))

async def test_database_connection():
    """Test connection to Kubernetes PostgreSQL"""
    try:
        from app.config import config
        import asyncpg
        
        print("🔍 Testing PostgreSQL connection...")
        print(f"   Host: {config.DB_HOST}")
        print(f"   Port: {config.DB_PORT}")
        print(f"   User: {config.DB_USER}")
        print(f"   Database: {config.database_name}")
        
        # Test connection to default postgres database first
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database='postgres'  # Connect to default database
        )
        
        # Check if our database exists
        result = await conn.fetch(
            "SELECT datname FROM pg_database WHERE datname = $1",
            config.database_name
        )
        
        if result:
            print(f"✅ Database '{config.database_name}' exists")
        else:
            print(f"❌ Database '{config.database_name}' does not exist")
            print("   Please create it manually or run the SQL setup script")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def setup_database_schema():
    """Run Alembic migrations to set up the schema"""
    try:
        print("\n🔄 Running database migrations...")
        
        # Run Alembic migrations
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=app_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

async def create_initial_users():
    """Create initial test users"""
    try:
        from app.database.connection import init_database, get_db_session
        from app.auth.user_repository import UserRepository
        from app.auth.password_utils import hash_password
        from app.database.models import User
        
        print("\n👤 Creating initial users...")
        
        # Initialize database
        await init_database()
        
        async with get_db_session() as session:
            user_repo = UserRepository(session)
            
            # Create test users
            users_to_create = [
                {
                    "email": "admin@pss-knowledge-assist.com",
                    "username": "PSS Admin", 
                    "password": "admin123"
                },
                {
                    "email": "test@pss-knowledge-assist.com",
                    "username": "Test User",
                    "password": "test123"
                }
            ]
            
            for user_data in users_to_create:
                existing = await user_repo.get_user_by_email(user_data["email"])
                
                if not existing:
                    user = User(
                        email=user_data["email"],
                        username=user_data["username"],
                        password_hash=hash_password(user_data["password"]),
                        is_active=True
                    )
                    
                    await user_repo.create_user(user)
                    print(f"✅ Created user: {user_data['email']}")
                else:
                    print(f"ℹ️  User already exists: {user_data['email']}")
            
            await session.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        return False

def print_connection_info():
    """Print connection information"""
    print("\n" + "="*60)
    print("🚀 PSS Knowledge Assist Setup Complete!")
    print("="*60)
    print("📋 Connection Information:")
    print("   Application URL: http://localhost:8080")
    print("   Database: PostgreSQL via Kubernetes port-forward")
    print("   Port Forward: localhost:5432 -> k8s postgres:5432")
    print()
    print("👤 Login Credentials:")
    print("   Admin: admin@pss-knowledge-assist.com / admin123")
    print("   Test:  test@pss-knowledge-assist.com / test123")
    print()
    print("🔧 Keep these terminals running:")
    print("   1. Port forward: kubectl port-forward service/postgres-service 5432:5432")
    print("   2. Application: python -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
    print("="*60)

async def main():
    """Main setup function"""
    print("🚀 PSS Knowledge Assist - Kubernetes Setup")
    print("="*50)
    
    # Test database connection
    if not await test_database_connection():
        print("\n❌ Database connection failed!")
        print("📋 Manual setup required:")
        print("1. Make sure port-forward is running:")
        print("   kubectl port-forward service/postgres-service 5432:5432")
        print("2. Create database manually:")
        print("   psql -h localhost -p 5432 -U postgres")
        print("   CREATE DATABASE pss_knowledge_assist_dev;")
        return False
    
    # Run migrations
    if not await setup_database_schema():
        print("\n❌ Schema setup failed!")
        return False
    
    # Create users
    if not await create_initial_users():
        print("\n❌ User creation failed!")
        return False
    
    # Success!
    print_connection_info()
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
