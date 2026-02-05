"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('careers_url', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_companies_id', 'companies', ['id'])
    op.create_index('ix_companies_name', 'companies', ['name'])
    op.create_index('ix_companies_domain', 'companies', ['domain'], unique=True)

    # Scrape sources table
    op.create_table(
        'scrape_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.Enum('greenhouse', 'lever', 'wttj', 'indeed', name='sourcetype'), nullable=False),
        sa.Column('base_url', sa.String(1024), nullable=False),
        sa.Column('risk_level', sa.Enum('low', 'medium', 'high', name='risklevel'), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_scraped_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scrape_sources_id', 'scrape_sources', ['id'])

    # Scrape runs table
    op.create_table(
        'scrape_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='runstatus'), nullable=True),
        sa.Column('jobs_found', sa.Integer(), nullable=True),
        sa.Column('jobs_new', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(2048), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['scrape_sources.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scrape_runs_id', 'scrape_runs', ['id'])

    # Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('dedup_hash', sa.String(64), nullable=True),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('job_type', sa.Enum('permanent', 'contract', 'unknown', name='jobtype'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(1024), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('salary_currency', sa.String(10), nullable=True),
        sa.Column('status', sa.Enum('raw', 'filtered_out', 'analyzing', 'scored', 'dismissed', 'applied', name='jobstatus'), nullable=True),
        sa.Column('filter_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['source_id'], ['scrape_sources.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_jobs_id', 'jobs', ['id'])
    op.create_index('ix_jobs_dedup_hash', 'jobs', ['dedup_hash'], unique=True)
    op.create_index('ix_jobs_status', 'jobs', ['status'])

    # LLM analyses table
    op.create_table(
        'llm_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('seniority_level', sa.String(50), nullable=True),
        sa.Column('detected_stack', sa.JSON(), nullable=True),
        sa.Column('required_experience_years', sa.Integer(), nullable=True),
        sa.Column('sponsorship_likelihood', sa.Float(), nullable=True),
        sa.Column('remote_policy', sa.String(50), nullable=True),
        sa.Column('team_size', sa.String(50), nullable=True),
        sa.Column('key_responsibilities', sa.JSON(), nullable=True),
        sa.Column('nice_to_haves', sa.JSON(), nullable=True),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index('ix_llm_analyses_id', 'llm_analyses', ['id'])

    # Job scores table
    op.create_table(
        'job_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('stack_match_score', sa.Float(), nullable=True),
        sa.Column('seniority_match_score', sa.Float(), nullable=True),
        sa.Column('sponsorship_score', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('stack_match_details', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index('ix_job_scores_id', 'job_scores', ['id'])
    op.create_index('ix_job_scores_total_score', 'job_scores', ['total_score'])

    # User preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cv_text', sa.Text(), nullable=True),
        sa.Column('target_stack', sa.JSON(), nullable=True),
        sa.Column('target_seniority', sa.String(50), nullable=True),
        sa.Column('target_location', sa.String(255), nullable=True),
        sa.Column('digest_enabled', sa.Boolean(), nullable=True),
        sa.Column('digest_hour_utc', sa.Integer(), nullable=True),
        sa.Column('digest_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_preferences_id', 'user_preferences', ['id'])

    # Digests table
    op.create_table(
        'digests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_ids', sa.JSON(), nullable=True),
        sa.Column('job_count', sa.Integer(), nullable=True),
        sa.Column('recipient_email', sa.String(255), nullable=True),
        sa.Column('subject', sa.String(512), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_digests_id', 'digests', ['id'])


def downgrade() -> None:
    op.drop_table('digests')
    op.drop_table('user_preferences')
    op.drop_table('job_scores')
    op.drop_table('llm_analyses')
    op.drop_table('jobs')
    op.drop_table('scrape_runs')
    op.drop_table('scrape_sources')
    op.drop_table('companies')

    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS jobtype")
    op.execute("DROP TYPE IF EXISTS runstatus")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS sourcetype")
