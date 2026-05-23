"""add announcements table

Revision ID: 77cdbf9d1d11
Revises: 20260518wechat
Create Date: 2026-05-23 09:30:35.409393

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77cdbf9d1d11'
down_revision = '20260518wechat'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create table if it doesn't exist
    if 'announcements' not in inspector.get_table_names():
        op.create_table(
            'announcements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('type', sa.String(length=20), nullable=True),
            sa.Column('target_role', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_announcements_id'), 'announcements', ['id'], unique=False)

    # Add composite index if table exists and index doesn't
    if 'announcements' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('announcements')]
        if 'idx_announcements_active_role_expires' not in existing_indexes:
            op.create_index('idx_announcements_active_role_expires', 'announcements',
                          ['is_active', 'target_role', 'expires_at'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Only drop if table exists
    if 'announcements' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('announcements')]

        # Drop composite index if it exists
        if 'idx_announcements_active_role_expires' in existing_indexes:
            op.drop_index('idx_announcements_active_role_expires', table_name='announcements')

        # Drop primary key index if it exists
        if 'ix_announcements_id' in existing_indexes:
            op.drop_index(op.f('ix_announcements_id'), table_name='announcements')

        # Drop table
        op.drop_table('announcements')
