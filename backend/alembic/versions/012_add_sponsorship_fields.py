"""Add sponsorship fields

Revision ID: 012
Revises: 011
Create Date: 2025-02-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('saved_analyses', sa.Column('offers_sponsorship', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('user_preferences', sa.Column('sponsorship_bonus_threshold', sa.Integer(), server_default='50', nullable=False))


def downgrade():
    op.drop_column('user_preferences', 'sponsorship_bonus_threshold')
    op.drop_column('saved_analyses', 'offers_sponsorship')
