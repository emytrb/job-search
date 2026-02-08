"""Add job_title and company_name to analysis_queue

Revision ID: 014
Revises: 013
Create Date: 2025-02-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('analysis_queue', sa.Column('job_title', sa.String(512), nullable=False, server_default=''))
    op.add_column('analysis_queue', sa.Column('company_name', sa.String(255), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('analysis_queue', 'company_name')
    op.drop_column('analysis_queue', 'job_title')
