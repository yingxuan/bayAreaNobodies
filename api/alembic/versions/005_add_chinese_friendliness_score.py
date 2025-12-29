"""Add chinese_friendliness_score to coupons table

Revision ID: 005_add_chinese_friendliness
Revises: 004_add_deals_fields
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_chinese_friendliness'
down_revision = '004_add_deals_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add chinese_friendliness_score column to coupons table
    op.add_column('coupons', sa.Column('chinese_friendliness_score', sa.Float(), nullable=True, server_default='0.0'))
    
    # Create index
    op.create_index(op.f('ix_coupons_chinese_friendliness_score'), 'coupons', ['chinese_friendliness_score'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_coupons_chinese_friendliness_score'), table_name='coupons')
    
    # Remove column
    op.drop_column('coupons', 'chinese_friendliness_score')

