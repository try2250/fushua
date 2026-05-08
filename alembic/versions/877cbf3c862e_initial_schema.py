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
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'field_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('field_key', sa.String(length=50), nullable=False),
        sa.Column('field_label', sa.String(length=100), nullable=False),
        sa.Column('field_type', sa.String(length=20), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=True),
        sa.Column('visible', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('options', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_field_configs_field_key'), 'field_configs', ['field_key'], unique=True)
    op.create_index(op.f('ix_field_configs_id'), 'field_configs', ['id'], unique=False)

    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=20), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=True),
        sa.Column('chapter', sa.String(length=100), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('q_type', sa.String(length=10), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('option_a', sa.String(length=500), nullable=True),
        sa.Column('option_b', sa.String(length=500), nullable=True),
        sa.Column('option_c', sa.String(length=500), nullable=True),
        sa.Column('option_d', sa.String(length=500), nullable=True),
        sa.Column('answer', sa.String(length=200), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    op.create_index('ix_questions_subject_chapter', 'questions', ['subject', 'chapter'], unique=False)
    op.create_index('ix_questions_subject_semester', 'questions', ['subject', 'semester'], unique=False)

    op.create_table(
        'records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('user_answer', sa.String(length=200), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_records_id'), 'records', ['id'], unique=False)
    op.create_index(op.f('ix_records_question_id'), 'records', ['question_id'], unique=False)
    op.create_index(op.f('ix_records_user_id'), 'records', ['user_id'], unique=False)
    op.create_index('ix_records_user_created', 'records', ['user_id', 'created_at'], unique=False)

    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'question_id', name='uq_favorite_user_question'),
    )
    op.create_index(op.f('ix_favorites_id'), 'favorites', ['id'], unique=False)
    op.create_index(op.f('ix_favorites_question_id'), 'favorites', ['question_id'], unique=False)
    op.create_index(op.f('ix_favorites_user_id'), 'favorites', ['user_id'], unique=False)

    op.create_table(
        'study_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=20), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=True),
        sa.Column('daily_goal', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_study_plans_id'), 'study_plans', ['id'], unique=False)
    op.create_index(op.f('ix_study_plans_user_id'), 'study_plans', ['user_id'], unique=False)

    op.create_table(
        'class_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_class_groups_id'), 'class_groups', ['id'], unique=False)

    op.create_table(
        'class_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['class_groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'user_id', name='uq_classmember_class_user'),
    )
    op.create_index(op.f('ix_class_members_class_id'), 'class_members', ['class_id'], unique=False)
    op.create_index(op.f('ix_class_members_id'), 'class_members', ['id'], unique=False)
    op.create_index(op.f('ix_class_members_user_id'), 'class_members', ['user_id'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('question_ids', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignments_id'), 'assignments', ['id'], unique=False)

    op.create_table(
        'assignment_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignment_records_assignment_id'), 'assignment_records', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_assignment_records_id'), 'assignment_records', ['id'], unique=False)
    op.create_index(op.f('ix_assignment_records_user_id'), 'assignment_records', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('assignment_records')
    op.drop_table('assignments')
    op.drop_table('notifications')
    op.drop_table('class_members')
    op.drop_table('class_groups')
    op.drop_table('study_plans')
    op.drop_table('favorites')
    op.drop_table('records')
    op.drop_table('questions')
    op.drop_table('field_configs')
    op.drop_table('users')
