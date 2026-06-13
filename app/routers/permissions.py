"""权限检查工具（Plan 1.2B 重构版）

- 不再有 'admin' role（合并到 teacher 或 platform_admin）
- 教师权限通过资源 created_by 字段直接判断
- 平台管理员通过 PlatformAdmin 表 + token 独立判断（参见 app/core/platform_auth.py）
"""
from sqlalchemy.orm import Session
from app.models import (
    ClassGroup, ClassMember, Question, QuestionBank, Assignment,
)


def teacher_owns_student(db: Session, teacher_id: int, student_id: int) -> bool:
    return db.query(ClassMember).join(
        ClassGroup, ClassGroup.id == ClassMember.class_id
    ).filter(
        ClassGroup.created_by == teacher_id,
        ClassMember.user_id == student_id,
    ).first() is not None


def teacher_owns_bank(db: Session, teacher_id: int, bank_id: int) -> bool:
    return db.query(QuestionBank).filter(
        QuestionBank.id == bank_id,
        QuestionBank.created_by == teacher_id,
    ).first() is not None


def teacher_owns_class(db: Session, teacher_id: int, class_id: int) -> bool:
    return db.query(ClassGroup).filter(
        ClassGroup.id == class_id,
        ClassGroup.created_by == teacher_id,
    ).first() is not None


def teacher_owns_question(db: Session, teacher_id: int, question_id: int) -> bool:
    return db.query(Question).filter(
        Question.id == question_id,
        Question.created_by == teacher_id,
    ).first() is not None


def teacher_owns_assignment(db: Session, teacher_id: int, assignment_id: int) -> bool:
    return db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.created_by == teacher_id,
    ).first() is not None
