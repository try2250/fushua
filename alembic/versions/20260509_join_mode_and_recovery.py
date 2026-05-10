"""add join_mode and recovery models

Revision ID: 20260509_join_mode
Revises: 20260509prod
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = "20260509_join_mode"
down_revision = "20260509prod"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade():
    if _table_exists("users") and not _column_exists("users", "join_mode"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.add_column(sa.Column("join_mode", sa.String(20), server_default="", nullable=True))

    if not _table_exists("class_join_requests"):
        op.create_table(
            "class_join_requests",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("class_id", sa.Integer(), nullable=False),
            sa.Column("display_name", sa.String(100), server_default=""),
            sa.Column("status", sa.String(20), server_default="pending"),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["class_id"], ["class_groups.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "class_id", name="uq_join_request_user_class"),
        )
        op.create_index(op.f("ix_class_join_requests_id"), "class_join_requests", ["id"], unique=False)
        op.create_index("ix_class_join_requests_user_id", "class_join_requests", ["user_id"], unique=False)
        op.create_index("ix_class_join_requests_class_id", "class_join_requests", ["class_id"], unique=False)

    if not _table_exists("account_recovery_requests"):
        op.create_table(
            "account_recovery_requests",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(50), nullable=False),
            sa.Column("class_id", sa.Integer(), nullable=True),
            sa.Column("display_name", sa.String(100), server_default=""),
            sa.Column("status", sa.String(20), server_default="pending"),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("new_password_hash", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.ForeignKeyConstraint(["class_id"], ["class_groups.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_account_recovery_requests_id"), "account_recovery_requests", ["id"], unique=False)
        op.create_index("ix_recovery_username", "account_recovery_requests", ["username"], unique=False)


def downgrade():
    if _table_exists("account_recovery_requests"):
        op.drop_table("account_recovery_requests")
    if _table_exists("class_join_requests"):
        op.drop_table("class_join_requests")
    if _table_exists("users") and _column_exists("users", "join_mode"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.drop_column("join_mode")
