"""Make job_url nullable and nullify localhost URLs

Revision ID: 011
Revises: 010
Create Date: 2025-02-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('saved_analyses', 'job_url', nullable=True)
    op.execute(
        "UPDATE saved_analyses SET job_url = NULL "
        "WHERE job_url LIKE '%localhost%' OR job_url = ''"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE saved_analyses SET job_url = '' WHERE job_url IS NULL"
    )
    op.alter_column('saved_analyses', 'job_url', nullable=False)
