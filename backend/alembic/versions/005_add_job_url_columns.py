"""add job_url columns

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add job_url to analysis_queue table
    op.add_column('analysis_queue', sa.Column('job_url', sa.String(2048), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE analysis_queue SET job_url = '' WHERE job_url IS NULL")
    # Make column non-nullable
    op.alter_column('analysis_queue', 'job_url', nullable=False)

    # Add job_url to saved_analyses table
    op.add_column('saved_analyses', sa.Column('job_url', sa.String(2048), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE saved_analyses SET job_url = '' WHERE job_url IS NULL")
    # Make column non-nullable
    op.alter_column('saved_analyses', 'job_url', nullable=False)


def downgrade() -> None:
    op.drop_column('saved_analyses', 'job_url')
    op.drop_column('analysis_queue', 'job_url')
