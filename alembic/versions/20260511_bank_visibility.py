"""add bank visibility and access_code

Revision ID: 20260511bank
Revises: 20260510_force_pwd
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa

revision = "20260511bank"
down_revision = "20260510_force_pwd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("question_banks", sa.Column("visibility", sa.String(20), server_default="public", nullable=True))
    op.add_column("question_banks", sa.Column("access_code", sa.String(50), server_default="", nullable=True))


def downgrade() -> None:
    op.drop_column("question_banks", "access_code")
    op.drop_column("question_banks", "visibility")
