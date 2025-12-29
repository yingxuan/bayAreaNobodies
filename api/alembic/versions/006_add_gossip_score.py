"""Add gossip_score to articles table

Revision ID: 006_add_gossip_score
Revises: 005_add_chinese_friendliness
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_gossip_score'
down_revision = '005_add_chinese_friendliness'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add gossip_score column to articles table
    op.add_column('articles', sa.Column('gossip_score', sa.Float(), nullable=True, server_default='0.0'))
    
    # Create index
    op.create_index(op.f('ix_articles_gossip_score'), 'articles', ['gossip_score'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_articles_gossip_score'), table_name='articles')
    
    # Remove column
    op.drop_column('articles', 'gossip_score')

