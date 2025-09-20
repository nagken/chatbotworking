"""Merge feedback into chat_responses and remove heavy data fields

Revision ID: 20241229_1400_002
Revises: 20241229_1200_001
Create Date: 2024-12-29 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '20241229_1400_002'
down_revision = '20241229_1200_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge feedback into chat_responses, remove heavy data fields, add insight, and remove query analytics"""
    
    # Step 1: Migrate existing feedback data to chat_responses table
    # Note: This is a data migration, we'll preserve existing data if any exists
    connection = op.get_bind()
    
    # Check if any feedback data exists to migrate
    feedback_exists = connection.execute(
        text("SELECT COUNT(*) FROM response_feedback")
    ).scalar()
    
    if feedback_exists > 0:
        # Migrate feedback data to chat_responses table by adding the fields first
        op.add_column('chat_responses', sa.Column('is_positive', sa.Boolean(), nullable=True))
        op.add_column('chat_responses', sa.Column('feedback_comment', sa.String(255), nullable=True))  # Limited to 255 chars
        op.add_column('chat_responses', sa.Column('feedback_user_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.add_column('chat_responses', sa.Column('feedback_created_at', sa.DateTime(timezone=True), nullable=True))
        op.add_column('chat_responses', sa.Column('feedback_updated_at', sa.DateTime(timezone=True), nullable=True))
        
        # Add foreign key constraint for feedback_user_id
        op.create_foreign_key(
            'fk_chat_responses_feedback_user_id', 
            'chat_responses', 
            'users', 
            ['feedback_user_id'], 
            ['id'], 
            ondelete='SET NULL'
        )
        
        # Migrate the data from response_feedback to chat_responses
        connection.execute(text("""
            UPDATE chat_responses 
            SET 
                is_positive = rf.is_positive,
                feedback_comment = rf.feedback_comment,
                feedback_user_id = rf.user_id,
                feedback_created_at = rf.created_at,
                feedback_updated_at = rf.updated_at
            FROM response_feedback rf 
            WHERE chat_responses.id = rf.response_id
        """))
    else:
        # No existing data, just add the columns
        op.add_column('chat_responses', sa.Column('is_positive', sa.Boolean(), nullable=True))
        op.add_column('chat_responses', sa.Column('feedback_comment', sa.String(255), nullable=True))  # Limited to 255 chars
        op.add_column('chat_responses', sa.Column('feedback_user_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.add_column('chat_responses', sa.Column('feedback_created_at', sa.DateTime(timezone=True), nullable=True))
        op.add_column('chat_responses', sa.Column('feedback_updated_at', sa.DateTime(timezone=True), nullable=True))
        
        # Add foreign key constraint for feedback_user_id
        op.create_foreign_key(
            'fk_chat_responses_feedback_user_id', 
            'chat_responses', 
            'users', 
            ['feedback_user_id'], 
            ['id'], 
            ondelete='SET NULL'
        )
    
    # Step 1.5: Add insight column to chat_responses 
    op.add_column('chat_responses', sa.Column('insight', sa.Text(), nullable=True))
    
    # Step 2: Drop the response_feedback table (after data migration)
    op.drop_table('response_feedback')
    
    # Step 3: Drop the query_analytics table (no longer needed)
    op.drop_table('query_analytics')
    
    # Step 4: Remove heavy data fields from chat_responses
    op.drop_column('chat_responses', 'raw_response')
    op.drop_column('chat_responses', 'execution_result')
    op.drop_column('chat_responses', 'chart_config')
    op.drop_column('chat_responses', 'processing_metadata')
    
    # Step 5: Drop old indexes that referenced removed fields
    op.drop_index('idx_responses_generated_sql', table_name='chat_responses')
    
    # Step 6: Create new indexes for feedback fields
    op.create_index('idx_responses_is_positive', 'chat_responses', ['is_positive'])
    op.create_index('idx_responses_feedback_user_id', 'chat_responses', ['feedback_user_id'])
    op.create_index('idx_responses_feedback_created_at', 'chat_responses', ['feedback_created_at'])
    
    # Step 7: Create unique constraint for one feedback per user per message (via response)
    op.create_index('uq_response_user_feedback', 'chat_responses', ['message_id', 'feedback_user_id'], unique=True)


def downgrade() -> None:
    """Reverse the migration - separate feedback back to its own table and recreate query analytics"""
    
    # Step 1: Recreate response_feedback table
    op.create_table('response_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('response_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_positive', sa.Boolean(), nullable=False),
        sa.Column('feedback_comment', sa.Text(), nullable=True),  # Back to unlimited text
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['response_id'], ['chat_responses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for response_feedback table
    op.create_index('idx_feedback_response_id', 'response_feedback', ['response_id'])
    op.create_index('idx_feedback_user_id', 'response_feedback', ['user_id'])
    op.create_index('idx_feedback_is_positive', 'response_feedback', ['is_positive'])
    op.create_index('idx_feedback_created_at', 'response_feedback', ['created_at'])
    op.create_index('uq_feedback_user_response', 'response_feedback', ['user_id', 'response_id'], unique=True)
    op.create_index(op.f('ix_response_feedback_id'), 'response_feedback', ['id'])
    
    # Step 1.5: Recreate query_analytics table
    op.create_table('query_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('superclient', sa.String(255), nullable=True),
        sa.Column('query_category', sa.String(100), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('sql_complexity_score', sa.Integer(), nullable=True),
        sa.Column('result_row_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for query_analytics table
    op.create_index('idx_analytics_user_id', 'query_analytics', ['user_id'])
    op.create_index('idx_analytics_message_id', 'query_analytics', ['message_id'])
    op.create_index('idx_analytics_superclient', 'query_analytics', ['superclient'])
    op.create_index('idx_analytics_category', 'query_analytics', ['query_category'])
    op.create_index('idx_analytics_created_at', 'query_analytics', ['created_at'])
    op.create_index(op.f('ix_query_analytics_id'), 'query_analytics', ['id'])
    
    # Step 2: Migrate feedback data back to response_feedback table
    connection = op.get_bind()
    
    # Check if any feedback data exists to migrate back
    feedback_exists = connection.execute(
        text("SELECT COUNT(*) FROM chat_responses WHERE feedback_user_id IS NOT NULL")
    ).scalar()
    
    if feedback_exists > 0:
        # Migrate the data back from chat_responses to response_feedback
        connection.execute(text("""
            INSERT INTO response_feedback (id, response_id, user_id, is_positive, feedback_comment, created_at, updated_at)
            SELECT 
                gen_random_uuid(),
                cr.id,
                cr.feedback_user_id,
                cr.is_positive,
                cr.feedback_comment,
                COALESCE(cr.feedback_created_at, cr.created_at),
                COALESCE(cr.feedback_updated_at, cr.created_at)
            FROM chat_responses cr 
            WHERE cr.feedback_user_id IS NOT NULL 
            AND cr.is_positive IS NOT NULL
        """))
    
    # Step 3: Drop feedback-related indexes from chat_responses
    op.drop_index('uq_response_user_feedback', table_name='chat_responses')
    op.drop_index('idx_responses_feedback_created_at', table_name='chat_responses')
    op.drop_index('idx_responses_feedback_user_id', table_name='chat_responses')
    op.drop_index('idx_responses_is_positive', table_name='chat_responses')
    
    # Step 4: Drop feedback-related foreign key constraint
    op.drop_constraint('fk_chat_responses_feedback_user_id', 'chat_responses', type_='foreignkey')
    
    # Step 5: Remove feedback columns and insight from chat_responses
    op.drop_column('chat_responses', 'feedback_updated_at')
    op.drop_column('chat_responses', 'feedback_created_at')
    op.drop_column('chat_responses', 'feedback_user_id')
    op.drop_column('chat_responses', 'feedback_comment')
    op.drop_column('chat_responses', 'is_positive')
    op.drop_column('chat_responses', 'insight')  # Remove insight column
    
    # Step 6: Re-add the heavy data fields to chat_responses
    op.add_column('chat_responses', sa.Column('raw_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('chat_responses', sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('chat_responses', sa.Column('chart_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('chat_responses', sa.Column('processing_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Step 7: Recreate the index for generated_sql
    op.create_index('idx_responses_generated_sql', 'chat_responses', ['generated_sql'])
