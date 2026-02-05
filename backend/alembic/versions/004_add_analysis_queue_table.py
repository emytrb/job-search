"""Add analysis_queue table

Revision ID: 004
Revises: 003
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'analysis_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        sa.Column('saved_analysis_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['saved_analysis_id'], ['saved_analyses.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_analysis_queue_id'), 'analysis_queue', ['id'], unique=False)
    op.create_index(op.f('ix_analysis_queue_status'), 'analysis_queue', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_analysis_queue_status'), table_name='analysis_queue')
    op.drop_index(op.f('ix_analysis_queue_id'), table_name='analysis_queue')
    op.drop_table('analysis_queue')
