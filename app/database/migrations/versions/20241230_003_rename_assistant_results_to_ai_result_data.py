"""Rename assistant_results table to ai_result_data

Revision ID: 20241230_003
Revises: 20241230_002
Create Date: 2024-12-30 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241230_003'
down_revision = '20241230_002'
branch_labels = None
depends_on = None


def upgrade():
    """Rename assistant_results table to ai_result_data and update all indexes"""
    
    # Rename the table
    op.rename_table('assistant_results', 'ai_result_data')
    
    # Drop old indexes
    op.drop_index('idx_assistant_results_message_id', table_name='ai_result_data')
    op.drop_index('idx_assistant_results_conversation_id', table_name='ai_result_data')
    op.drop_index('idx_assistant_results_user_id', table_name='ai_result_data')
    op.drop_index('idx_assistant_results_chunk_index', table_name='ai_result_data')
    op.drop_index('idx_assistant_results_created_at', table_name='ai_result_data')
    op.drop_index('idx_assistant_results_data_validation_status', table_name='ai_result_data')
    op.drop_index('idx_assistant_results_message_chunk', table_name='ai_result_data')
    op.drop_constraint('uq_assistant_result_chunk', 'ai_result_data', type_='unique')
    
    # Create new indexes with updated names
    op.create_index('idx_ai_result_data_message_id', 'ai_result_data', ['message_id'])
    op.create_index('idx_ai_result_data_conversation_id', 'ai_result_data', ['conversation_id'])
    op.create_index('idx_ai_result_data_user_id', 'ai_result_data', ['user_id'])
    op.create_index('idx_ai_result_data_chunk_index', 'ai_result_data', ['chunk_index'])
    op.create_index('idx_ai_result_data_created_at', 'ai_result_data', ['created_at'])
    op.create_index('idx_ai_result_data_data_validation_status', 'ai_result_data', ['data_validation_status'])
    
    # Create composite indexes
    op.create_index('idx_ai_result_data_message_chunk', 'ai_result_data', ['message_id', 'chunk_index'])
    
    # Create unique constraint for chunks per message
    op.create_unique_constraint('uq_ai_result_data_chunk', 'ai_result_data', ['message_id', 'chunk_index'])


def downgrade():
    """Rename ai_result_data table back to assistant_results and restore old indexes"""
    
    # Drop new indexes
    op.drop_index('idx_ai_result_data_message_id', table_name='ai_result_data')
    op.drop_index('idx_ai_result_data_conversation_id', table_name='ai_result_data')
    op.drop_index('idx_ai_result_data_user_id', table_name='ai_result_data')
    op.drop_index('idx_ai_result_data_chunk_index', table_name='ai_result_data')
    op.drop_index('idx_ai_result_data_created_at', table_name='ai_result_data')
    op.drop_index('idx_ai_result_data_data_validation_status', table_name='ai_result_data')
    op.drop_index('idx_ai_result_data_message_chunk', table_name='ai_result_data')
    op.drop_constraint('uq_ai_result_data_chunk', 'ai_result_data', type_='unique')
    
    # Restore old indexes
    op.create_index('idx_assistant_results_message_id', 'ai_result_data', ['message_id'])
    op.create_index('idx_assistant_results_conversation_id', 'ai_result_data', ['conversation_id'])
    op.create_index('idx_assistant_results_user_id', 'ai_result_data', ['user_id'])
    op.create_index('idx_assistant_results_chunk_index', 'ai_result_data', ['chunk_index'])
    op.create_index('idx_assistant_results_created_at', 'ai_result_data', ['created_at'])
    op.create_index('idx_assistant_results_data_validation_status', 'ai_result_data', ['data_validation_status'])
    op.create_index('idx_assistant_results_message_chunk', 'ai_result_data', ['message_id', 'chunk_index'])
    op.create_unique_constraint('uq_assistant_result_chunk', 'ai_result_data', ['message_id', 'chunk_index'])
    
    # Rename the table back
    op.rename_table('ai_result_data', 'assistant_results')
