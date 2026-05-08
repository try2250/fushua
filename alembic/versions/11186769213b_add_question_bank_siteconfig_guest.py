"""add_question_bank_siteconfig_guest

Revision ID: 11186769213b
Revises: 877cbf3c862e
Create Date: 2026-05-08 21:10:16.785262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '11186769213b'
down_revision: Union[str, None] = '877cbf3c862e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name):
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not _table_exists('question_banks'):
        op.create_table('question_banks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=20), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bank_type', sa.String(length=20), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table('question_banks', schema=None) as batch_op:
            batch_op.create_index('ix_question_banks_subject', ['subject'], unique=False)

    if not _table_exists('site_configs'):
        op.create_table('site_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table('site_configs', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_site_configs_key'), ['key'], unique=True)

    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bank_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_questions_bank_id'), ['bank_id'], unique=False)
        batch_op.create_foreign_key('fk_questions_bank_id', 'question_banks', ['bank_id'], ['id'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_guest', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('guest_expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('class_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_class_id'), ['class_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_class_id'))
        batch_op.drop_column('is_admin')
        batch_op.drop_column('class_id')
        batch_op.drop_column('guest_expires_at')
        batch_op.drop_column('is_guest')

    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_questions_bank_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_questions_bank_id'))
        batch_op.drop_column('bank_id')

    op.drop_table('site_configs')

    op.drop_table('question_banks')
