"""Add deal-specific fields to coupons table

Revision ID: 004_add_deals_fields
Revises: 003_add_video_thumbnail
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_deals_fields'
down_revision = '003_add_video_thumbnail'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add deal-specific fields to coupons table
    op.add_column('coupons', sa.Column('canonical_url', sa.Text(), nullable=True))
    op.add_column('coupons', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.add_column('coupons', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('coupons', sa.Column('score', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('coupons', sa.Column('source', sa.String(), nullable=True))
    op.add_column('coupons', sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    
    # Create indexes
    op.create_index(op.f('ix_coupons_canonical_url'), 'coupons', ['canonical_url'], unique=False)
    op.create_index(op.f('ix_coupons_content_hash'), 'coupons', ['content_hash'], unique=False)
    op.create_index(op.f('ix_coupons_score'), 'coupons', ['score'], unique=False)
    op.create_index(op.f('ix_coupons_source'), 'coupons', ['source'], unique=False)
    op.create_index(op.f('ix_coupons_fetched_at'), 'coupons', ['fetched_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_coupons_fetched_at'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_source'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_score'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_content_hash'), table_name='coupons')
    op.drop_index(op.f('ix_coupons_canonical_url'), table_name='coupons')
    
    # Remove columns
    op.drop_column('coupons', 'fetched_at')
    op.drop_column('coupons', 'source')
    op.drop_column('coupons', 'score')
    op.drop_column('coupons', 'published_at')
    op.drop_column('coupons', 'content_hash')
    op.drop_column('coupons', 'canonical_url')

