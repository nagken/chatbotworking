#!/usr/bin/env python3
"""
Check and create database tables for CVS Pharmacy webapp
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def check_and_create_tables():
    """Check existing tables and create missing ones"""
    
    # Connection parameters
    conn_params = {
        'host': '34.66.64.233',
        'database': 'cvs_pharmacy_dev',
        'user': 'postgres',
        'password': 'CvsPharmacy2024!',
        'port': 5432
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check existing tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        existing_tables = [table[0] for table in cur.fetchall()]
        
        print("✅ Existing tables in database:")
        for table in existing_tables:
            print(f"  - {table}")
        
        # Required tables for chat functionality
        required_tables = [
            'users',
            'chat_conversations', 
            'chat_messages',
            'user_sessions'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"\n❌ Missing tables: {missing_tables}")
            
            # Create missing tables in correct order (users first)
            if 'users' in missing_tables:
                print("📝 Creating users table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) UNIQUE NOT NULL,
                        username VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_login_at TIMESTAMP WITH TIME ZONE
                    );
                """)
                
            if 'chat_conversations' in missing_tables:
                print("📝 Creating chat_conversations table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_conversations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id VARCHAR(255) NOT NULL,
                        conversation_id VARCHAR(255) UNIQUE NOT NULL,
                        title VARCHAR(500) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                
            if 'chat_messages' in missing_tables:
                print("📝 Creating chat_messages table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        conversation_id UUID REFERENCES chat_conversations(id) ON DELETE CASCADE,
                        role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        feedback_score INTEGER CHECK (feedback_score IN (-1, 1)),
                        feedback_user_id UUID
                    );
                """)
                
            if 'user_sessions' in missing_tables:
                print("📝 Creating user_sessions table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
            
            print("✅ Created missing tables!")
        else:
            print("\n✅ All required tables exist!")
        
        # Verify final state
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        final_tables = [table[0] for table in cur.fetchall()]
        
        print(f"\n📊 Final database state ({len(final_tables)} tables):")
        for table in sorted(final_tables):
            print(f"  ✅ {table}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = check_and_create_tables()
    if success:
        print("\n🎉 Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed!")