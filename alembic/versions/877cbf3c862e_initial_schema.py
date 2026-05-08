"""initial_schema

Revision ID: 877cbf3c862e
Revises:
Create Date: 2026-05-08 18:34:20.743372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '877cbf3c862e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('class_members', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_classmember_class_user', ['class_id', 'user_id'])

    with op.batch_alter_table('favorites', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_favorite_user_question', ['user_id', 'question_id'])

    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.create_index('ix_questions_subject_chapter', ['subject', 'chapter'], unique=False)
        batch_op.create_index('ix_questions_subject_semester', ['subject', 'semester'], unique=False)

    with op.batch_alter_table('records', schema=None) as batch_op:
        batch_op.create_index('ix_records_user_created', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('records', schema=None) as batch_op:
        batch_op.drop_index('ix_records_user_created')

    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_index('ix_questions_subject_semester')
        batch_op.drop_index('ix_questions_subject_chapter')

    with op.batch_alter_table('favorites', schema=None) as batch_op:
        batch_op.drop_constraint('uq_favorite_user_question', type_='unique')

    with op.batch_alter_table('class_members', schema=None) as batch_op:
        batch_op.drop_constraint('uq_classmember_class_user', type_='unique')
