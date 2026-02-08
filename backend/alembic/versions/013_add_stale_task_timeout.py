"""Add stale task timeout

Revision ID: 013
Revises: 012
Create Date: 2025-02-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('user_preferences', sa.Column('stale_task_timeout_minutes', sa.Integer(), server_default='10', nullable=False))


def downgrade() -> None:
    op.drop_column('user_preferences', 'stale_task_timeout_minutes')
