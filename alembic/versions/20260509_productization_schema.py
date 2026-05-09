"""productization_schema

Revision ID: 20260509prod
Revises: 11186769213b
Create Date: 2026-05-09 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260509prod"
down_revision: Union[str, None] = "11186769213b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if _table_exists("users") and not _column_exists("users", "is_disabled"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.add_column(sa.Column("is_disabled", sa.Boolean(), nullable=True))

    if _table_exists("assignments") and not _column_exists("assignments", "class_id"):
        with op.batch_alter_table("assignments", schema=None) as batch_op:
            batch_op.add_column(sa.Column("class_id", sa.Integer(), nullable=True))
            batch_op.create_index(batch_op.f("ix_assignments_class_id"), ["class_id"], unique=False)

    if not _table_exists("mastery_records"):
        op.create_table(
            "mastery_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("consecutive_correct", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "question_id", name="uq_mastery_user_question"),
        )
        op.create_index(op.f("ix_mastery_records_id"), "mastery_records", ["id"], unique=False)
        op.create_index(op.f("ix_mastery_records_question_id"), "mastery_records", ["question_id"], unique=False)
        op.create_index(op.f("ix_mastery_records_user_id"), "mastery_records", ["user_id"], unique=False)

    if not _table_exists("feedbacks"):
        op.create_table(
            "feedbacks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("role", sa.String(length=10), nullable=True),
            sa.Column("page_path", sa.String(length=500), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_feedbacks_id"), "feedbacks", ["id"], unique=False)

    if not _table_exists("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("target_type", sa.String(length=50), nullable=True),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("detail", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
        op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"], unique=False)
        op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)


def downgrade() -> None:
    if _table_exists("audit_logs"):
        op.drop_table("audit_logs")
    if _table_exists("feedbacks"):
        op.drop_table("feedbacks")
    if _table_exists("mastery_records"):
        op.drop_table("mastery_records")
    if _table_exists("assignments") and _column_exists("assignments", "class_id"):
        with op.batch_alter_table("assignments", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_assignments_class_id"))
            batch_op.drop_column("class_id")
    if _table_exists("users") and _column_exists("users", "is_disabled"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.drop_column("is_disabled")
