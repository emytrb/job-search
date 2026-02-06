"""add last_analyzed_at to saved_analyses

Revision ID: 007
Revises: 006
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('saved_analyses', sa.Column('last_analyzed_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE saved_analyses SET last_analyzed_at = created_at")
    op.alter_column('saved_analyses', 'last_analyzed_at', nullable=False, server_default=sa.text('now()'))


def downgrade() -> None:
    op.drop_column('saved_analyses', 'last_analyzed_at')
