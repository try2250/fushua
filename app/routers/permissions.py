from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import ClassGroup, ClassMember, QuestionBank, Question


def teacher_owns_student(db: Session, teacher_id: int, student_id: int) -> bool:
    """检查学生是否属于该教师创建的班级"""
    teacher_classes = select(ClassGroup.id).where(ClassGroup.created_by == teacher_id)
    return db.query(ClassMember).filter(
        ClassMember.class_id.in_(teacher_classes),
        ClassMember.user_id == student_id,
    ).first() is not None


def teacher_owns_bank(db: Session, teacher_id: int, bank_id: int) -> bool:
    """检查题库是否属于该教师"""
    return db.query(QuestionBank).filter(
        QuestionBank.id == bank_id,
        QuestionBank.created_by == teacher_id,
    ).first() is not None


def teacher_owns_class(db: Session, teacher_id: int, class_id: int) -> bool:
    """检查班级是否属于该教师"""
    return db.query(ClassGroup).filter(
        ClassGroup.id == class_id,
        ClassGroup.created_by == teacher_id,
    ).first() is not None


def teacher_owns_question(db: Session, teacher_id: int, question_id: int) -> bool:
    """检查题目是否属于该教师"""
    return db.query(Question).filter(
        Question.id == question_id,
        Question.created_by == teacher_id,
    ).first() is not None
