"""Add description_simhash to saved_analyses and similarity_threshold to user_preferences

Revision ID: 010
Revises: 009
Create Date: 2025-02-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

from app.utils.simhash import compute_simhash

# revision identifiers
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable column first (for backfill)
    op.add_column('saved_analyses', sa.Column('description_simhash', sa.BigInteger(), nullable=True))

    # Add similarity_threshold to user_preferences
    op.add_column('user_preferences', sa.Column('similarity_threshold', sa.Integer(), server_default='90', nullable=False))

    # Backfill existing rows
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, job_description FROM saved_analyses")).fetchall()
    for row in rows:
        simhash = compute_simhash(row[1])
        conn.execute(
            sa.text("UPDATE saved_analyses SET description_simhash = :hash WHERE id = :id"),
            {"hash": simhash, "id": row[0]},
        )

    # Make non-null after backfill
    op.alter_column('saved_analyses', 'description_simhash', nullable=False)


def downgrade() -> None:
    op.drop_column('saved_analyses', 'description_simhash')
    op.drop_column('user_preferences', 'similarity_threshold')
