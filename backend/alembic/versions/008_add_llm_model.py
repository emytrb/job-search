"""add llm_model to saved_analyses

Revision ID: 008
Revises: 007
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('saved_analyses', sa.Column('llm_model', sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column('saved_analyses', 'llm_model')
