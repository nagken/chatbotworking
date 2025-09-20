"""PSS Knowledge Assist initial schema

Revision ID: 20250909_001_pss_initial_schema
Revises: 
Create Date: 2025-09-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250909_001_pss_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=False)
    op.create_index('idx_users_active', 'users', ['is_active'], unique=False)
    op.create_index('idx_users_created_at', 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('remember_me', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sessions_user_id', 'user_sessions', ['user_id'], unique=False)
    op.create_index('idx_sessions_token', 'user_sessions', ['session_token'], unique=False)
    op.create_index('idx_sessions_expires', 'user_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=True)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)

    # Create chat_conversations table
    op.create_table('chat_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversations_user_id', 'chat_conversations', ['user_id'], unique=False)
    op.create_index('idx_conversations_created_at', 'chat_conversations', ['created_at'], unique=False)
    op.create_index('idx_conversations_updated_at', 'chat_conversations', ['updated_at'], unique=False)
    op.create_index(op.f('ix_chat_conversations_id'), 'chat_conversations', ['id'], unique=False)

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_type', sa.Enum('USER', 'ASSISTANT', name='messagetype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('feedback_rating', sa.String(length=20), nullable=True),
        sa.Column('feedback_comment', sa.Text(), nullable=True),
        sa.Column('feedback_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feedback_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['feedback_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_messages_conversation_id', 'chat_messages', ['conversation_id'], unique=False)
    op.create_index('idx_messages_user_id', 'chat_messages', ['user_id'], unique=False)
    op.create_index('idx_messages_created_at', 'chat_messages', ['created_at'], unique=False)
    op.create_index('idx_messages_message_type', 'chat_messages', ['message_type'], unique=False)
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_index('idx_messages_message_type', table_name='chat_messages')
    op.drop_index('idx_messages_created_at', table_name='chat_messages')
    op.drop_index('idx_messages_user_id', table_name='chat_messages')
    op.drop_index('idx_messages_conversation_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index(op.f('ix_chat_conversations_id'), table_name='chat_conversations')
    op.drop_index('idx_conversations_updated_at', table_name='chat_conversations')
    op.drop_index('idx_conversations_created_at', table_name='chat_conversations')
    op.drop_index('idx_conversations_user_id', table_name='chat_conversations')
    op.drop_table('chat_conversations')
    
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_session_token'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_id'), table_name='user_sessions')
    op.drop_index('idx_sessions_expires', table_name='user_sessions')
    op.drop_index('idx_sessions_token', table_name='user_sessions')
    op.drop_index('idx_sessions_user_id', table_name='user_sessions')
    op.drop_table('user_sessions')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_active', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
