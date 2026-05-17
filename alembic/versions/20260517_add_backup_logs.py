"""add backup_logs table

Revision ID: 20260517backup
Revises: 20260511bank
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa

revision = "20260517backup"
down_revision = "20260511bank"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backup_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("triggered_by", sa.String(50), server_default="cron", nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backup_logs_id"), "backup_logs", ["id"], unique=False)
    op.create_index(op.f("ix_backup_logs_created_at"), "backup_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_backup_logs_status"), "backup_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_backup_logs_status"), table_name="backup_logs")
    op.drop_index(op.f("ix_backup_logs_created_at"), table_name="backup_logs")
    op.drop_index(op.f("ix_backup_logs_id"), table_name="backup_logs")
    op.drop_table("backup_logs")
