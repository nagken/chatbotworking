"""Initial database schema with users and chat tables

Revision ID: 20241229_1200_001
Revises: 
Create Date: 2024-12-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '20241229_1200_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all initial tables for the CA Rebates Tool"""
    
    # Handle ENUM type for message types
    connection = op.get_bind()
    
    # Check if the enum already exists
    enum_exists = connection.execute(
        text("SELECT 1 FROM pg_type WHERE typname = 'messagetype'")
    ).fetchone()
    
    if not enum_exists:
        # Create the enum only if it doesn't exist
        connection.execute(text("CREATE TYPE messagetype AS ENUM ('USER', 'ASSISTANT')"))
    
    # Define the enum for use in table creation
    message_type_enum = postgresql.ENUM('USER', 'ASSISTANT', name='messagetype', create_type=False)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index(op.f('ix_users_id'), 'users', ['id'])
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('remember_me', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )
    
    # Create indexes for user_sessions table
    op.create_index('idx_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_sessions_token', 'user_sessions', ['session_token'])
    op.create_index('idx_sessions_expires', 'user_sessions', ['expires_at'])
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'])
    
    # Create chat_conversations table
    op.create_table('chat_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for chat_conversations table
    op.create_index('idx_conversations_user_id', 'chat_conversations', ['user_id'])
    op.create_index('idx_conversations_conversation_id', 'chat_conversations', ['conversation_id'])
    op.create_index('idx_conversations_created_at', 'chat_conversations', ['created_at'])
    op.create_index(op.f('ix_chat_conversations_id'), 'chat_conversations', ['id'])
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_type', message_type_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('superclient', sa.String(length=255), nullable=True),
        sa.Column('enhanced_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for chat_messages table
    op.create_index('idx_messages_conversation_id', 'chat_messages', ['conversation_id'])
    op.create_index('idx_messages_user_id', 'chat_messages', ['user_id'])
    op.create_index('idx_messages_type', 'chat_messages', ['message_type'])
    op.create_index('idx_messages_superclient', 'chat_messages', ['superclient'])
    op.create_index('idx_messages_created_at', 'chat_messages', ['created_at'])
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'])
    
    # Create chat_responses table
    op.create_table('chat_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_sql', sa.Text(), nullable=True),
        sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('chart_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for chat_responses table
    op.create_index('idx_responses_message_id', 'chat_responses', ['message_id'])
    op.create_index('idx_responses_success', 'chat_responses', ['success'])
    op.create_index('idx_responses_created_at', 'chat_responses', ['created_at'])
    op.create_index('idx_responses_generated_sql', 'chat_responses', ['generated_sql'])
    op.create_index(op.f('ix_chat_responses_id'), 'chat_responses', ['id'])
    
    # Create query_analytics table
    op.create_table('query_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('superclient', sa.String(length=255), nullable=True),
        sa.Column('query_category', sa.String(length=100), nullable=True),
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
    
    # Create response_feedback table
    op.create_table('response_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('response_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_positive', sa.Boolean(), nullable=False),
        sa.Column('feedback_comment', sa.Text(), nullable=True),
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


def downgrade() -> None:
    """Drop all tables - reverses the upgrade"""
    
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('response_feedback')
    op.drop_table('query_analytics')
    op.drop_table('chat_responses')
    op.drop_table('chat_messages')
    op.drop_table('chat_conversations')
    op.drop_table('user_sessions')
    op.drop_table('users')
    
    # Drop ENUM type (only if it exists and no other objects depend on it)
    connection = op.get_bind()
    enum_exists = connection.execute(
        text("SELECT 1 FROM pg_type WHERE typname = 'messagetype'")
    ).fetchone()
    
    if enum_exists:
        # Use raw SQL to drop the enum type
        connection.execute(text("DROP TYPE IF EXISTS messagetype"))
