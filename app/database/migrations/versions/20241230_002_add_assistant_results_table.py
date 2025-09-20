"""Add AssistantResult table and result_schema field

Revision ID: 20241230_002
Revises: 20241230_001
Create Date: 2024-12-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241230_002'
down_revision = '20241230_001'
branch_labels = None
depends_on = None


def upgrade():
    """Add AssistantResult table and result_schema field to ChatMessage"""
    
    # Add result_schema field to chat_messages table
    op.add_column('chat_messages', 
                  sa.Column('result_schema', postgresql.JSONB(), nullable=True))
    
    # Create index on result_schema
    op.create_index('idx_messages_result_schema', 'chat_messages', ['result_schema'], 
                    postgresql_using='gin')
    
    # Create assistant_results table
    op.create_table('assistant_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False),
        sa.Column('result_data', postgresql.JSONB(), nullable=False),
        sa.Column('data_validation_status', sa.String(length=50), nullable=False),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for assistant_results table
    op.create_index('idx_assistant_results_message_id', 'assistant_results', ['message_id'])
    op.create_index('idx_assistant_results_conversation_id', 'assistant_results', ['conversation_id'])
    op.create_index('idx_assistant_results_user_id', 'assistant_results', ['user_id'])
    op.create_index('idx_assistant_results_chunk_index', 'assistant_results', ['chunk_index'])
    op.create_index('idx_assistant_results_created_at', 'assistant_results', ['created_at'])
    op.create_index('idx_assistant_results_data_validation_status', 'assistant_results', ['data_validation_status'])
    
    # Create composite indexes
    op.create_index('idx_assistant_results_message_chunk', 'assistant_results', ['message_id', 'chunk_index'])
    
    # Create unique constraint for chunks per message
    op.create_unique_constraint('uq_assistant_result_chunk', 'assistant_results', ['message_id', 'chunk_index'])


def downgrade():
    """Remove AssistantResult table and result_schema field"""
    
    # Drop assistant_results table (this will also drop all indexes and constraints)
    op.drop_table('assistant_results')
    
    # Drop result_schema index
    op.drop_index('idx_messages_result_schema', table_name='chat_messages')
    
    # Drop result_schema column
    op.drop_column('chat_messages', 'result_schema')
