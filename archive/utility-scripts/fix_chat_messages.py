#!/usr/bin/env python3
"""
Fix chat_messages table to add missing user_id column
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_chat_messages_table():
    """Add missing user_id column to chat_messages table"""
    
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
        
        print("🔧 Fixing chat_messages table...")
        
        # Check current columns in chat_messages table
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        current_columns = cur.fetchall()
        
        print("📋 Current chat_messages columns:")
        for col in current_columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check if user_id column exists
        has_user_id = any(col[0] == 'user_id' for col in current_columns)
        
        if not has_user_id:
            print("\n❌ Missing user_id column - adding it...")
            
            # Add user_id column
            cur.execute("""
                ALTER TABLE chat_messages 
                ADD COLUMN user_id VARCHAR(255) NOT NULL DEFAULT 'admin-user-id';
            """)
            
            print("✅ Added user_id column to chat_messages")
            
            # Create index for performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);")
            print("✅ Created index on user_id column")
        else:
            print("✅ user_id column already exists")
        
        # Verify final structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        final_columns = cur.fetchall()
        
        print(f"\n📊 Final chat_messages structure ({len(final_columns)} columns):")
        for col in final_columns:
            print(f"  ✅ {col[0]}: {col[1]} (nullable: {col[2]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = fix_chat_messages_table()
    if success:
        print("\n🎉 chat_messages table fix completed successfully!")
        print("✅ user_id column is now available for message storage")
        print("✅ Database should now support real LLM conversations")
    else:
        print("\n❌ chat_messages table fix failed!")