"""add retry columns to analysis_queue

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add retry_count column with default 0
    op.add_column('analysis_queue', sa.Column('retry_count', sa.Integer(), nullable=True))
    op.execute("UPDATE analysis_queue SET retry_count = 0 WHERE retry_count IS NULL")
    op.alter_column('analysis_queue', 'retry_count', nullable=False)

    # Add max_retries column with default 3
    op.add_column('analysis_queue', sa.Column('max_retries', sa.Integer(), nullable=True))
    op.execute("UPDATE analysis_queue SET max_retries = 3 WHERE max_retries IS NULL")
    op.alter_column('analysis_queue', 'max_retries', nullable=False)


def downgrade() -> None:
    op.drop_column('analysis_queue', 'max_retries')
    op.drop_column('analysis_queue', 'retry_count')
