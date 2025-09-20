"""Add message chunks table and remove ai_result_data

Revision ID: 20241231_001
Revises: 20241230_004_remove_result_data_index
Create Date: 2024-12-31 10:00:00.000000

This migration:
1. Creates MessageChunkType enum for chunk types
2. Creates message_chunks table for storing streaming response chunks
3. Removes the old ai_result_data table (replaced by message_chunks)
4. Updates relationships to use message_chunks instead of ai_result_data

The new message_chunks system stores individual transformed chunks from streaming responses,
preventing PostgreSQL btree v4 index size limit errors by using smaller, more manageable chunks.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241231_001'
down_revision = '20241230_004'
branch_labels = None
depends_on = None


def upgrade():
    """Apply the migration"""
    
    # Create MessageChunkType enum (handle case where it already exists)
    connection = op.get_bind()
    
    # Check if the enum already exists
    enum_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type 
            WHERE typname = 'messagechunktype'
        );
    """)).scalar()
    
    if not enum_exists:
        message_chunk_type_enum = postgresql.ENUM(
            'sql', 'data', 'chart', 'insights',
            name='messagechunktype',
            create_type=True
        )
        message_chunk_type_enum.create(connection, checkfirst=False)
        print("[SUCCESS] Created MessageChunkType enum")
    else:
        print("[INFO] MessageChunkType enum already exists, skipping creation")
    
    # Create the enum type for table creation
    message_chunk_type_enum = postgresql.ENUM(
        'sql', 'data', 'chart', 'insights',
        name='messagechunktype',
        create_type=False  # Don't create, just reference existing
    )
    
    # Check if message_chunks table already exists
    table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'message_chunks'
        );
    """)).scalar()
    
    if not table_exists:
        # Create message_chunks table
        op.create_table(
            'message_chunks',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('chunk_type', message_chunk_type_enum, nullable=False),
            sa.Column('chunk_sequence', sa.Integer(), nullable=False),
            sa.Column('data_chunk_index', sa.Integer(), nullable=False, default=0),
            sa.Column('total_data_chunks', sa.Integer(), nullable=False, default=1),
            sa.Column('chunk_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            
            # Foreign key constraints
            sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
            
            # Primary key
            sa.PrimaryKeyConstraint('id'),
        )
        print("[SUCCESS] Created message_chunks table")
    else:
        print("[INFO] message_chunks table already exists, skipping creation")
    
    # Create indexes for efficient querying (only if table was created)
    if not table_exists:
        try:
            op.create_index('idx_message_chunks_message_id', 'message_chunks', ['message_id'])
            op.create_index('idx_message_chunks_type', 'message_chunks', ['chunk_type'])
            op.create_index('idx_message_chunks_sequence', 'message_chunks', ['chunk_sequence'])
            op.create_index('idx_message_chunks_data_index', 'message_chunks', ['data_chunk_index'])
            op.create_index('idx_message_chunks_created_at', 'message_chunks', ['created_at'])
            
            # Composite indexes for efficient retrieval
            op.create_index('idx_message_chunks_message_type', 'message_chunks', ['message_id', 'chunk_type'])
            op.create_index('idx_message_chunks_message_sequence', 'message_chunks', ['message_id', 'chunk_sequence'])
            op.create_index('idx_message_chunks_message_data_chunk', 'message_chunks', ['message_id', 'chunk_type', 'data_chunk_index'])
            
            # Unique constraint to ensure unique data chunks per message and chunk type
            op.create_index('uq_message_chunks_data_chunk', 'message_chunks', ['message_id', 'chunk_type', 'data_chunk_index'], unique=True)
            
            print("[SUCCESS] Created indexes for message_chunks table")
        except Exception as e:
            print(f"[WARNING] Some indexes may already exist: {e}")
    else:
        print("[INFO] Skipping index creation since table already exists")
    
    # Drop the old ai_result_data table (if it exists)
    # This table is being replaced by the new message_chunks approach
    ai_table_exists = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'ai_result_data'
        );
    """)).scalar()
    
    if ai_table_exists:
        try:
            op.drop_table('ai_result_data')
            print("[SUCCESS] Dropped ai_result_data table")
        except Exception as e:
            print(f"[WARNING] Failed to drop ai_result_data table: {e}")
    else:
        print("[INFO] ai_result_data table doesn't exist, no need to drop it")
    
    print("[SUCCESS] Migration completed: Added message_chunks table and removed ai_result_data")


def downgrade():
    """Reverse the migration"""
    
    # Drop message_chunks table and its indexes
    op.drop_index('uq_message_chunks_data_chunk', table_name='message_chunks')
    op.drop_index('idx_message_chunks_message_data_chunk', table_name='message_chunks')
    op.drop_index('idx_message_chunks_message_sequence', table_name='message_chunks')
    op.drop_index('idx_message_chunks_message_type', table_name='message_chunks')
    op.drop_index('idx_message_chunks_created_at', table_name='message_chunks')
    op.drop_index('idx_message_chunks_data_index', table_name='message_chunks')
    op.drop_index('idx_message_chunks_sequence', table_name='message_chunks')
    op.drop_index('idx_message_chunks_type', table_name='message_chunks')
    op.drop_index('idx_message_chunks_message_id', table_name='message_chunks')
    
    op.drop_table('message_chunks')
    
    # Drop the MessageChunkType enum
    message_chunk_type_enum = postgresql.ENUM(name='messagechunktype')
    message_chunk_type_enum.drop(op.get_bind(), checkfirst=True)
    
    # Recreate ai_result_data table (basic structure for rollback compatibility)
    # This is a simplified version - you may need to run the original migrations
    # to fully restore the previous state
    op.create_table(
        'ai_result_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, default=0),
        sa.Column('total_chunks', sa.Integer(), nullable=False, default=1),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('data_validation_status', sa.String(50), nullable=False, default='valid'),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Recreate basic indexes (without the problematic result_data index)
    op.create_index('idx_ai_result_data_message_id', 'ai_result_data', ['message_id'])
    op.create_index('idx_ai_result_data_conversation_id', 'ai_result_data', ['conversation_id'])
    op.create_index('idx_ai_result_data_user_id', 'ai_result_data', ['user_id'])
    op.create_index('idx_ai_result_data_chunk_index', 'ai_result_data', ['chunk_index'])
    op.create_index('idx_ai_result_data_created_at', 'ai_result_data', ['created_at'])
    
    print("[WARNING] Rollback completed: Restored ai_result_data table (basic structure)")
    print("[WARNING] Note: You may need to run 'python scripts/run_database_migration.py upgrade 20241230_004' to fully restore the original state")
