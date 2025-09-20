"""Enhanced message storage - add SQL query, chart config, and AI insights to chat_messages

Revision ID: 20241230_001
Revises: 20241229_1400_002
Create Date: 2024-12-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241230_001'
down_revision = '20241229_1400_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced message storage fields to chat_messages table"""
    
    # Add new columns to chat_messages table
    op.add_column('chat_messages', sa.Column('sql_query', sa.Text(), nullable=True))
    op.add_column('chat_messages', sa.Column('chart_config', postgresql.JSONB(), nullable=True))
    op.add_column('chat_messages', sa.Column('ai_insights', sa.Text(), nullable=True))
    op.add_column('chat_messages', sa.Column('response_metadata', postgresql.JSONB(), nullable=True))
    
    # Add indexes for new columns
    op.create_index('idx_messages_sql_query', 'chat_messages', ['sql_query'])
    op.create_index('idx_messages_chart_config', 'chat_messages', ['chart_config'], postgresql_using='gin')
    op.create_index('idx_messages_ai_insights', 'chat_messages', ['ai_insights'])
    
    # Add comment explaining the new fields
    op.execute("""
        COMMENT ON COLUMN chat_messages.sql_query IS 'Generated SQL query for re-execution';
        COMMENT ON COLUMN chat_messages.chart_config IS 'Chart configuration without data values for re-rendering';
        COMMENT ON COLUMN chat_messages.ai_insights IS 'AI insights about the data analysis';
        COMMENT ON COLUMN chat_messages.response_metadata IS 'Additional metadata about the response (timing, success, etc.)';
    """)


def downgrade() -> None:
    """Remove enhanced message storage fields from chat_messages table"""
    
    # Drop indexes
    op.drop_index('idx_messages_ai_insights', 'chat_messages')
    op.drop_index('idx_messages_chart_config', 'chat_messages')
    op.drop_index('idx_messages_sql_query', 'chat_messages')
    
    # Drop columns
    op.drop_column('chat_messages', 'response_metadata')
    op.drop_column('chat_messages', 'ai_insights')
    op.drop_column('chat_messages', 'chart_config')
    op.drop_column('chat_messages', 'sql_query')
