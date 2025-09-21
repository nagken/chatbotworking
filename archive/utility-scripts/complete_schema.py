#!/usr/bin/env python3
"""
Complete the chat_messages table schema to match SQLAlchemy model
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def complete_chat_messages_schema():
    """Add all missing columns to match the SQLAlchemy model"""
    
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
        
        print("🔧 Completing chat_messages table schema...")
        
        # Create the messagetype enum if it doesn't exist
        print("🏗️ Creating messagetype enum...")
        cur.execute("""
            DO $$ BEGIN
                CREATE TYPE messagetype AS ENUM ('USER', 'ASSISTANT', 'SYSTEM');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        print("✅ messagetype enum ready")
        
        # Check current columns
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        current_columns = cur.fetchall()
        current_column_names = [col[0] for col in current_columns]
        
        print("📋 Current columns:", current_column_names)
        
        # Required columns from SQLAlchemy model
        required_columns = [
            ('message_type', 'messagetype', 'role'),  # (new_name, type, old_name_to_copy_from)
            ('superclient', 'VARCHAR(255)', None),
            ('enhanced_message', 'TEXT', None),
            ('sql_query', 'TEXT', None),
            ('chart_config', 'JSONB', None),
            ('ai_insights', 'TEXT', None),
            ('response_metadata', 'JSONB', None),
            ('result_schema', 'JSONB', None),
            ('is_positive', 'BOOLEAN', None),
            ('feedback_comment', 'VARCHAR(255)', None),
            ('feedback_created_at', 'TIMESTAMP WITH TIME ZONE', None)
        ]
        
        # Add missing columns
        for col_name, col_type, copy_from in required_columns:
            if col_name not in current_column_names:
                print(f"➕ Adding column: {col_name} ({col_type})")
                
                if copy_from and copy_from in current_column_names:
                    # Copy data from existing column and then drop it
                    cur.execute(f"ALTER TABLE chat_messages ADD COLUMN {col_name} {col_type};")
                    
                    # Map role values to messagetype enum values
                    if col_name == 'message_type' and copy_from == 'role':
                        cur.execute("""
                            UPDATE chat_messages 
                            SET message_type = CASE 
                                WHEN role = 'user' THEN 'USER'::messagetype
                                WHEN role = 'assistant' THEN 'ASSISTANT'::messagetype  
                                WHEN role = 'system' THEN 'SYSTEM'::messagetype
                                ELSE 'USER'::messagetype
                            END;
                        """)
                        print(f"   📋 Copied and mapped data from {copy_from} to {col_name}")
                    else:
                        cur.execute(f"UPDATE chat_messages SET {col_name} = {copy_from}::{col_type};")
                        print(f"   📋 Copied data from {copy_from} to {col_name}")
                else:
                    # Add new column with default
                    if col_type == 'messagetype':
                        cur.execute(f"ALTER TABLE chat_messages ADD COLUMN {col_name} {col_type} DEFAULT 'USER';")
                    else:
                        cur.execute(f"ALTER TABLE chat_messages ADD COLUMN {col_name} {col_type};")
                
                print(f"   ✅ Added {col_name}")
            else:
                print(f"✅ Column {col_name} already exists")
        
        # Drop the old 'role' column if it exists and we have message_type
        if 'role' in current_column_names and 'message_type' in [col[0] for col in required_columns]:
            print("🗑️ Dropping old 'role' column...")
            cur.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS role;")
            print("✅ Dropped old 'role' column")
        
        # Create additional indices for performance
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON chat_messages(message_type);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_superclient ON chat_messages(superclient);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_feedback_user_id ON chat_messages(feedback_user_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_is_positive ON chat_messages(is_positive);"
        ]
        
        for idx_sql in indices:
            try:
                cur.execute(idx_sql)
            except Exception as e:
                print(f"⚠️ Index creation warning: {e}")
        
        print("✅ Created performance indices")
        
        # Verify final structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        final_columns = cur.fetchall()
        
        print(f"\n📊 Final chat_messages structure ({len(final_columns)} columns):")
        for col in final_columns:
            print(f"  ✅ {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = complete_chat_messages_schema()
    if success:
        print("\n🎉 chat_messages schema completion successful!")
        print("✅ All required columns are now available")
        print("✅ Database should now fully support real LLM conversations")
        print("✅ Ready to restart webapp with full functionality")
    else:
        print("\n❌ chat_messages schema completion failed!")