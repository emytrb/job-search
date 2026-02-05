"""Add analyzer guidelines fields

Revision ID: 002
Revises: 001
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_preferences', sa.Column('ats_guidelines', sa.Text(), nullable=True))
    op.add_column('user_preferences', sa.Column('job_requirements_context', sa.Text(), nullable=True))
    op.add_column('user_preferences', sa.Column('cover_letter_guidelines', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_preferences', 'cover_letter_guidelines')
    op.drop_column('user_preferences', 'job_requirements_context')
    op.drop_column('user_preferences', 'ats_guidelines')
