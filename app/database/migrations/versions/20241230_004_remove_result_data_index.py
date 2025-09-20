"""Remove index on result_data column to prevent size limit errors

Revision ID: 20241230_004
Revises: 20241230_003
Create Date: 2024-12-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241230_004'
down_revision = '20241230_003'
branch_labels = None
depends_on = None


def upgrade():
    """Remove the index on result_data column to prevent PostgreSQL index size limit errors"""
    
    # Drop the index on result_data column if it exists
    # This prevents the "index row requires X bytes, maximum size is 8191" error
    try:
        op.drop_index('idx_ai_result_data_result_data', table_name='ai_result_data')
    except:
        # Index might not exist, which is fine
        pass


def downgrade():
    """Recreate the index on result_data column (not recommended due to size issues)"""
    
    # Note: This is not recommended as it will likely cause the same size limit errors
    # Only uncomment if you're sure the data sizes are manageable
    # op.create_index('idx_ai_result_data_result_data', 'ai_result_data', ['result_data'])
    pass
