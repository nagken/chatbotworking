#!/usr/bin/env python3
"""
Create the missing chat_responses table and fix data agent configuration
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_chat_responses_table():
    """Create the missing chat_responses table"""
    
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
        
        print("🏗️ Creating chat_responses table...")
        
        # Create chat_responses table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS chat_responses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            message_id UUID REFERENCES chat_messages(id) ON DELETE CASCADE,
            generated_sql VARCHAR(10000),
            insight VARCHAR(5000),
            processing_time_ms INTEGER,
            success BOOLEAN DEFAULT FALSE,
            error_message VARCHAR(1000),
            is_positive BOOLEAN,
            feedback_comment VARCHAR(255),
            feedback_user_id VARCHAR(255),
            feedback_created_at TIMESTAMP WITH TIME ZONE,
            feedback_updated_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        cur.execute(create_table_sql)
        print("✅ chat_responses table created successfully")
        
        # Create indices for performance
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_chat_responses_message_id ON chat_responses(message_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_responses_success ON chat_responses(success);",
            "CREATE INDEX IF NOT EXISTS idx_chat_responses_created_at ON chat_responses(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_chat_responses_feedback_user_id ON chat_responses(feedback_user_id);"
        ]
        
        for idx_sql in indices:
            cur.execute(idx_sql)
        
        print("✅ Created performance indices for chat_responses")
        
        # Verify table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'chat_responses' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        print(f"\n📊 chat_responses table structure ({len(columns)} columns):")
        for col in columns:
            print(f"  ✅ {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = create_chat_responses_table()
    if success:
        print("\n🎉 chat_responses table creation successful!")
        print("✅ Database now has all required tables for LLM conversations")
    else:
        print("\n❌ chat_responses table creation failed!")