"""add force_password_change field

Revision ID: 20260510_force_pwd
Revises: 20260509_join_mode
Create Date: 2026-05-10
"""
from alembic import op
import sqlalchemy as sa

revision = "20260510_force_pwd"
down_revision = "20260509_join_mode"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("force_password_change", sa.Boolean(), server_default="0", nullable=True))


def downgrade():
    op.drop_column("users", "force_password_change")
