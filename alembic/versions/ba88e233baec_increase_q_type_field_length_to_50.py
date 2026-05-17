"""increase q_type field length to 50

Revision ID: ba88e233baec
Revises: 20260517backup
Create Date: 2026-05-17 16:31:11.060317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ba88e233baec'
down_revision: Union[str, None] = '20260517backup'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 扩大 q_type 字段长度从 10 到 50
    op.alter_column('questions', 'q_type',
                    existing_type=sa.String(length=10),
                    type_=sa.String(length=50),
                    existing_nullable=False)


def downgrade() -> None:
    # 恢复 q_type 字段长度到 10
    op.alter_column('questions', 'q_type',
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=10),
                    existing_nullable=False)
