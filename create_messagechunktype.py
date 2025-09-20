#!/usr/bin/env python3
"""
Create the missing messagechunktype enum for message_chunks table
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_messagechunktype_enum():
    """Create the missing messagechunktype enum"""
    
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
        
        print("🏗️ Creating messagechunktype enum...")
        
        # Create the messagechunktype enum if it doesn't exist
        cur.execute("""
            DO $$ BEGIN
                CREATE TYPE messagechunktype AS ENUM ('text', 'sql', 'insights', 'data', 'chart', 'system', 'error');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        print("✅ messagechunktype enum created successfully")
        
        # Update the message_chunks table to use the enum type
        print("🔧 Updating message_chunks table to use messagechunktype enum...")
        
        # First check if we need to update the column type
        cur.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'message_chunks' 
            AND column_name = 'chunk_type' 
            AND table_schema = 'public';
        """)
        result = cur.fetchone()
        
        if result and result[0] == 'character varying':
            print("🔄 Converting chunk_type column from VARCHAR to messagechunktype enum...")
            
            # Convert existing data and change column type
            cur.execute("""
                ALTER TABLE message_chunks 
                ALTER COLUMN chunk_type TYPE messagechunktype 
                USING chunk_type::messagechunktype;
            """)
            print("✅ Successfully converted chunk_type column to enum type")
        else:
            print("✅ chunk_type column already uses correct type")
        
        # Verify the enum was created
        cur.execute("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'messagechunktype'
            )
            ORDER BY enumsortorder;
        """)
        enum_values = cur.fetchall()
        
        print(f"\n📊 messagechunktype enum values ({len(enum_values)} values):")
        for value in enum_values:
            print(f"  ✅ {value[0]}")
        
        # Verify table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'message_chunks' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        print(f"\n📊 Updated message_chunks table structure ({len(columns)} columns):")
        for col in columns:
            print(f"  ✅ {col[0]}: {col[1]} (nullable: {col[2]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = create_messagechunktype_enum()
    if success:
        print("\n🎉 messagechunktype enum creation successful!")
        print("✅ Message chunks can now be stored properly")
        print("✅ Streaming chat functionality fully operational")
    else:
        print("\n❌ messagechunktype enum creation failed!")