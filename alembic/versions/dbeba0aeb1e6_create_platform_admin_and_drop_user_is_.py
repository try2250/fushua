"""create platform_admin table (drop user.is_admin deferred to Task 5)

Revision ID: dbeba0aeb1e6
Revises: 77cdbf9d1d11
Create Date: 2026-06-13 11:18:58.172439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'dbeba0aeb1e6'
down_revision: Union[str, None] = '77cdbf9d1d11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('platform_admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('platform_admins', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_platform_admins_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_platform_admins_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_platform_admins_username'), ['username'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('platform_admins', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_platform_admins_username'))
        batch_op.drop_index(batch_op.f('ix_platform_admins_id'))
        batch_op.drop_index(batch_op.f('ix_platform_admins_email'))
    op.drop_table('platform_admins')
