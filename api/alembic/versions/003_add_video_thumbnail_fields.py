"""Add video_id and thumbnail_url fields to articles

Revision ID: 003_add_video_thumbnail
Revises: 001_initial
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_video_thumbnail'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add video_id and thumbnail_url columns to articles table
    op.add_column('articles', sa.Column('video_id', sa.String(), nullable=True))
    op.add_column('articles', sa.Column('thumbnail_url', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove video_id and thumbnail_url columns
    op.drop_column('articles', 'thumbnail_url')
    op.drop_column('articles', 'video_id')

