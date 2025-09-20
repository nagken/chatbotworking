#!/usr/bin/env python3
"""
Create the missing message_chunks table for streaming message reconstruction
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_message_chunks_table():
    """Create the missing message_chunks table"""
    
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
        
        print("🏗️ Creating message_chunks table...")
        
        # Create message_chunks table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS message_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            message_id UUID REFERENCES chat_messages(id) ON DELETE CASCADE,
            chunk_type VARCHAR(50) NOT NULL,
            chunk_sequence INTEGER NOT NULL,
            data_chunk_index INTEGER,
            total_data_chunks INTEGER,
            chunk_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        cur.execute(create_table_sql)
        print("✅ message_chunks table created successfully")
        
        # Create indices for performance
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_message_chunks_message_id ON message_chunks(message_id);",
            "CREATE INDEX IF NOT EXISTS idx_message_chunks_sequence ON message_chunks(chunk_sequence);",
            "CREATE INDEX IF NOT EXISTS idx_message_chunks_type ON message_chunks(chunk_type);",
            "CREATE INDEX IF NOT EXISTS idx_message_chunks_message_sequence ON message_chunks(message_id, chunk_sequence, data_chunk_index);"
        ]
        
        for idx_sql in indices:
            cur.execute(idx_sql)
        
        print("✅ Created performance indices for message_chunks")
        
        # Verify table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'message_chunks' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        print(f"\n📊 message_chunks table structure ({len(columns)} columns):")
        for col in columns:
            print(f"  ✅ {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = create_message_chunks_table()
    if success:
        print("\n🎉 message_chunks table creation successful!")
        print("✅ Database now has all required tables for complete functionality")
        print("✅ Streaming message reconstruction will now work properly")
    else:
        print("\n❌ message_chunks table creation failed!")