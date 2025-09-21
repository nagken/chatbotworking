#!/usr/bin/env python3
"""
Fix database schema to handle string user IDs properly
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_database_schema():
    """Fix database schema for string user IDs"""
    
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
        
        print("🔧 Fixing database schema for string user IDs...")
        
        # Drop existing tables in the correct order (reverse of creation)
        print("📝 Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS user_sessions CASCADE;")
        cur.execute("DROP TABLE IF EXISTS chat_messages CASCADE;")
        cur.execute("DROP TABLE IF EXISTS chat_conversations CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        
        # Recreate tables with proper string user ID handling
        print("📝 Creating users table with UUID primary key...")
        cur.execute("""
            CREATE TABLE users (
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
        
        print("📝 Creating chat_conversations table with string user_id...")
        cur.execute("""
            CREATE TABLE chat_conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL,
                conversation_id VARCHAR(255) UNIQUE NOT NULL,
                title VARCHAR(500) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        print("📝 Creating chat_messages table...")
        cur.execute("""
            CREATE TABLE chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                conversation_id UUID REFERENCES chat_conversations(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                feedback_score INTEGER CHECK (feedback_score IN (-1, 1)),
                feedback_user_id VARCHAR(255)
            );
        """)
        
        print("📝 Creating user_sessions table with string user_id...")
        cur.execute("""
            CREATE TABLE user_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Add indices for performance
        print("📝 Creating indices...")
        cur.execute("CREATE INDEX idx_chat_conversations_user_id ON chat_conversations(user_id);")
        cur.execute("CREATE INDEX idx_chat_conversations_conversation_id ON chat_conversations(conversation_id);")
        cur.execute("CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);")
        cur.execute("CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);")
        cur.execute("CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);")
        
        # Verify final state
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        final_tables = [table[0] for table in cur.fetchall()]
        
        print(f"\n📊 Database schema fixed successfully ({len(final_tables)} tables):")
        for table in sorted(final_tables):
            print(f"  ✅ {table}")
        
        # Show table structures for verification
        for table in ['users', 'chat_conversations', 'chat_messages', 'user_sessions']:
            print(f"\n🔍 Structure of {table}:")
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND table_schema = 'public'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print("\n🎉 Database schema fix completed successfully!")
        print("✅ String user IDs are now properly supported")
        print("✅ All foreign key constraints use appropriate types")
        print("✅ Performance indices have been added")
    else:
        print("\n❌ Database schema fix failed!")