"""add wechat and phone fields to users

Revision ID: 20260518wechat
Revises: ba88e233baec
Create Date: 2026-05-18

"""
from alembic import op
import sqlalchemy as sa


revision = '20260518wechat'
down_revision = 'ba88e233baec'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('openid', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('is_phone_verified', sa.Boolean(), server_default='false'))
        batch_op.add_column(sa.Column('avatar_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('nickname', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('wechat_unionid', sa.String(100), nullable=True))
        batch_op.create_unique_constraint('uq_users_phone', ['phone'])
        batch_op.create_unique_constraint('uq_users_openid', ['openid'])
        batch_op.create_index('idx_users_phone', ['phone'])
        batch_op.create_index('idx_users_openid', ['openid'])

    op.create_table(
        'verification_codes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('purpose', sa.String(20), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='false'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_verification_codes_phone_expires', 'verification_codes', ['phone', 'expires_at'])


def downgrade():
    op.drop_index('idx_verification_codes_phone_expires', 'verification_codes')
    op.drop_table('verification_codes')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('idx_users_openid')
        batch_op.drop_index('idx_users_phone')
        batch_op.drop_constraint('uq_users_openid')
        batch_op.drop_constraint('uq_users_phone')
        batch_op.drop_column('wechat_unionid')
        batch_op.drop_column('nickname')
        batch_op.drop_column('avatar_url')
        batch_op.drop_column('is_phone_verified')
        batch_op.drop_column('openid')
        batch_op.drop_column('phone')
