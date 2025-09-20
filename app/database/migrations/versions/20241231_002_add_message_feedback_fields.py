"""Add user feedback fields to chat_messages table

Revision ID: 20241231_002
Revises: 20241231_001
Create Date: 2024-12-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241231_002'
down_revision = '20241231_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user feedback fields to chat_messages table"""
    
    # Add new feedback columns to chat_messages table
    op.add_column('chat_messages', sa.Column('is_positive', sa.Boolean(), nullable=True))
    op.add_column('chat_messages', sa.Column('feedback_comment', sa.String(length=255), nullable=True))
    op.add_column('chat_messages', sa.Column('feedback_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('chat_messages', sa.Column('feedback_created_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add foreign key constraint for feedback_user_id
    op.create_foreign_key(
        'fk_messages_feedback_user_id',
        'chat_messages', 'users',
        ['feedback_user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for new columns
    op.create_index('idx_messages_is_positive', 'chat_messages', ['is_positive'])
    op.create_index('idx_messages_feedback_user_id', 'chat_messages', ['feedback_user_id'])
    op.create_index('idx_messages_feedback_created_at', 'chat_messages', ['feedback_created_at'])
    
    # Add composite indexes for efficient feedback queries
    op.create_index('idx_messages_feedback_composite', 'chat_messages', ['message_type', 'is_positive'])
    op.create_index('idx_messages_user_feedback', 'chat_messages', ['feedback_user_id', 'feedback_created_at'])
    
    # Add unique constraint: one feedback per user per message
    op.create_index('uq_message_user_feedback', 'chat_messages', ['id', 'feedback_user_id'], unique=True)
    
    # Add comments explaining the new fields
    op.execute("""
        COMMENT ON COLUMN chat_messages.is_positive IS 'User feedback: True = thumbs up, False = thumbs down, NULL = no feedback';
        COMMENT ON COLUMN chat_messages.feedback_comment IS 'Optional feedback comment from user (max 255 chars)';
        COMMENT ON COLUMN chat_messages.feedback_user_id IS 'User who provided the feedback (foreign key to users.id)';
        COMMENT ON COLUMN chat_messages.feedback_created_at IS 'Timestamp when feedback was provided';
    """)


def downgrade() -> None:
    """Remove user feedback fields from chat_messages table"""
    
    # Drop indexes
    op.drop_index('uq_message_user_feedback', 'chat_messages')
    op.drop_index('idx_messages_user_feedback', 'chat_messages')
    op.drop_index('idx_messages_feedback_composite', 'chat_messages')
    op.drop_index('idx_messages_feedback_created_at', 'chat_messages')
    op.drop_index('idx_messages_feedback_user_id', 'chat_messages')
    op.drop_index('idx_messages_is_positive', 'chat_messages')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_messages_feedback_user_id', 'chat_messages', type_='foreignkey')
    
    # Drop columns
    op.drop_column('chat_messages', 'feedback_created_at')
    op.drop_column('chat_messages', 'feedback_user_id')
    op.drop_column('chat_messages', 'feedback_comment')
    op.drop_column('chat_messages', 'is_positive')
