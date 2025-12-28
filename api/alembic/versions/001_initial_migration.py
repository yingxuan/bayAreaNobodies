"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create source_queries table
    op.create_table(
        'source_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('site_domain', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('interval_min', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_queries_id'), 'source_queries', ['id'], unique=False)
    op.create_index(op.f('ix_source_queries_source_type'), 'source_queries', ['source_type'], unique=False)

    # Create search_results_raw table
    op.create_table(
        'search_results_raw',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('raw_json', sa.Text(), nullable=True),
        sa.Column('search_rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['query_id'], ['source_queries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_results_raw_id'), 'search_results_raw', ['id'], unique=False)

    # Create articles table
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('normalized_url', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('cleaned_text', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('summary_bullets', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('city_hints', sa.Text(), nullable=True),
        sa.Column('company_tags', sa.Text(), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('saves', sa.Integer(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('freshness_score', sa.Float(), nullable=True),
        sa.Column('search_rank_score', sa.Float(), nullable=True),
        sa.Column('final_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_normalized_url'), 'articles', ['normalized_url'], unique=False)
    op.create_index(op.f('ix_articles_url'), 'articles', ['url'], unique=False)
    op.create_index(op.f('ix_articles_content_hash'), 'articles', ['content_hash'], unique=False)
    op.create_index(op.f('ix_articles_source_type'), 'articles', ['source_type'], unique=False)
    op.create_index(op.f('ix_articles_final_score'), 'articles', ['final_score'], unique=False)
    op.create_index('idx_articles_source_score', 'articles', ['source_type', 'final_score'], unique=False)

    # Create trending_snapshots table
    op.create_table(
        'trending_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trending_snapshots_id'), 'trending_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_trending_snapshots_source_type'), 'trending_snapshots', ['source_type'], unique=False)
    op.create_index(op.f('ix_trending_snapshots_snapshot_at'), 'trending_snapshots', ['snapshot_at'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('preferred_city', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create holdings table
    op.create_table(
        'holdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('cost_basis', sa.Float(), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_holdings_id'), 'holdings', ['id'], unique=False)
    op.create_index(op.f('ix_holdings_ticker'), 'holdings', ['ticker'], unique=False)

    # Create coupons table
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('terms', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coupons_id'), 'coupons', ['id'], unique=False)
    op.create_index(op.f('ix_coupons_city'), 'coupons', ['city'], unique=False)
    op.create_index(op.f('ix_coupons_category'), 'coupons', ['category'], unique=False)

    # Create digests table
    op.create_table(
        'digests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('digest_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_digests_id'), 'digests', ['id'], unique=False)
    op.create_index(op.f('ix_digests_digest_date'), 'digests', ['digest_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_digests_digest_date'), table_name='digests')
    op.drop_index(op.f('ix_digests_id'), table_name='digests')
    op.drop_table('digests')
    op.drop_index(op.f('ix_coupons_category'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_city'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_id'), table_name='coupons')
    op.drop_table('coupons')
    op.drop_index(op.f('ix_holdings_ticker'), table_name='holdings')
    op.drop_index(op.f('ix_holdings_id'), table_name='holdings')
    op.drop_table('holdings')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_trending_snapshots_snapshot_at'), table_name='trending_snapshots')
    op.drop_index(op.f('ix_trending_snapshots_source_type'), table_name='trending_snapshots')
    op.drop_index(op.f('ix_trending_snapshots_id'), table_name='trending_snapshots')
    op.drop_table('trending_snapshots')
    op.drop_index('idx_articles_source_score', table_name='articles')
    op.drop_index(op.f('ix_articles_final_score'), table_name='articles')
    op.drop_index(op.f('ix_articles_source_type'), table_name='articles')
    op.drop_index(op.f('ix_articles_content_hash'), table_name='articles')
    op.drop_index(op.f('ix_articles_url'), table_name='articles')
    op.drop_index(op.f('ix_articles_normalized_url'), table_name='articles')
    op.drop_index(op.f('ix_articles_id'), table_name='articles')
    op.drop_table('articles')
    op.drop_index(op.f('ix_search_results_raw_id'), table_name='search_results_raw')
    op.drop_table('search_results_raw')
    op.drop_index(op.f('ix_source_queries_source_type'), table_name='source_queries')
    op.drop_index(op.f('ix_source_queries_id'), table_name='source_queries')
    op.drop_table('source_queries')

