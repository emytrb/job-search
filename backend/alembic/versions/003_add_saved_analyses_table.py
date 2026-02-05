"""Add saved_analyses table

Revision ID: 003
Revises: 002
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'saved_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_title', sa.String(512), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('job_description', sa.Text(), nullable=False),
        sa.Column('eligibility_status', sa.String(50), nullable=False),
        sa.Column('eligibility_reasons', sa.JSON(), nullable=False),
        sa.Column('matching_score', sa.Integer(), nullable=False),
        sa.Column('matching_explanation', sa.Text(), nullable=False),
        sa.Column('key_requirements', sa.JSON(), nullable=False),
        sa.Column('resume_suggestions', sa.JSON(), nullable=False),
        sa.Column('ats_keywords', sa.JSON(), nullable=False),
        sa.Column('cover_letter', sa.Text(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_saved_analyses_id'), 'saved_analyses', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_saved_analyses_id'), table_name='saved_analyses')
    op.drop_table('saved_analyses')
