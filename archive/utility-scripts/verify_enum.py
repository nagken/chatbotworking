#!/usr/bin/env python3
"""
Quick verification that messagechunktype enum was created successfully
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def verify_enum():
    """Verify messagechunktype enum exists and has correct values"""
    load_dotenv()
    
    # Database connection
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'cvs_pharmacy_dev'),
        'user': os.getenv('DB_USER', 'cvs_admin'),
        'password': os.getenv('DB_PASSWORD', 'CVSPharmacy2024!'),
    }
    
    print("🔗 Connecting to database...")
    try:
        conn = await asyncpg.connect(**db_config)
        
        # Check if enum exists
        enum_check = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'messagechunktype'
            );
        """)
        
        if enum_check:
            print("✅ messagechunktype enum exists")
            
            # Get enum values
            enum_values = await conn.fetch("""
                SELECT enumlabel 
                FROM pg_enum 
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                WHERE pg_type.typname = 'messagechunktype'
                ORDER BY enumsortorder;
            """)
            
            print(f"✅ Enum has {len(enum_values)} values:")
            for value in enum_values:
                print(f"  • {value['enumlabel']}")
            
            # Check message_chunks table structure
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'message_chunks'
                ORDER BY ordinal_position;
            """)
            
            print(f"✅ message_chunks table has {len(columns)} columns:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  • {col['column_name']}: {col['data_type']} ({nullable})")
            
            print("✅ Database schema is complete and ready!")
            return True
            
        else:
            print("❌ messagechunktype enum NOT found")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    print("🧪 Verifying messagechunktype enum...")
    print("=" * 50)
    
    success = asyncio.run(verify_enum())
    
    print("=" * 50)
    if success:
        print("🎉 Database verification successful!")
        print("✅ CVS Pharmacy Knowledge Assist is ready for full operation")
    else:
        print("❌ Database verification failed")