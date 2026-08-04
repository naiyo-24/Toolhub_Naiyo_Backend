"""Add company profile fields to users

Revision ID: 414fa0ecbd5e
Revises: 20976a1d8f3a
Create Date: 2026-07-27 18:51:40.911152

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '414fa0ecbd5e'
down_revision = '20976a1d8f3a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('company_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('company_logo_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('company_address', sa.String(), nullable=True))
    op.add_column('users', sa.Column('whatsapp_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('gst_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('business_type', sa.String(), nullable=True))
    op.add_column('users', sa.Column('bank_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('account_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('account_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('ifsc_code', sa.String(), nullable=True))
    op.add_column('users', sa.Column('pricing_mode', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'pricing_mode')
    op.drop_column('users', 'ifsc_code')
    op.drop_column('users', 'account_number')
    op.drop_column('users', 'account_name')
    op.drop_column('users', 'bank_name')
    op.drop_column('users', 'business_type')
    op.drop_column('users', 'gst_number')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'whatsapp_number')
    op.drop_column('users', 'company_address')
    op.drop_column('users', 'company_logo_url')
    op.drop_column('users', 'company_name')
