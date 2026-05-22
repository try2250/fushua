from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import ClassGroup, ClassMember, QuestionBank, Question, User
from app.utils.logger import log_warning


def is_admin(db: Session, user_id: int) -> bool:
    """检查用户是否是管理员"""
    user = db.query(User).filter(User.id == user_id).first()
    return user is not None and (user.role == "admin" or user.is_admin)


def teacher_owns_student(db: Session, teacher_id: int, student_id: int) -> bool:
    """检查学生是否属于该教师创建的班级，管理员可以查看所有学生"""
    if is_admin(db, teacher_id):
        return True
    teacher_classes = select(ClassGroup.id).where(ClassGroup.created_by == teacher_id)
    is_member = db.query(ClassMember).filter(
        ClassMember.class_id.in_(teacher_classes),
        ClassMember.user_id == student_id,
    ).first() is not None

    if not is_member:
        # 只在学生存在但不属于该教师时记录权限拒绝
        student_exists = db.query(User).filter(User.id == student_id).first() is not None
        if student_exists:
            log_warning(
                "Permission denied: teacher does not own student",
                teacher_id=teacher_id,
                student_id=student_id,
                resource_type="student"
            )

    return is_member


def teacher_owns_bank(db: Session, teacher_id: int, bank_id: int) -> bool:
    """检查题库是否属于该教师，管理员可以查看所有题库"""
    if is_admin(db, teacher_id):
        return True
    bank = db.query(QuestionBank).filter(
        QuestionBank.id == bank_id,
        QuestionBank.created_by == teacher_id,
    ).first()

    if bank is None:
        # 只在题库存在但不属于该教师时记录权限拒绝
        bank_exists = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first() is not None
        if bank_exists:
            log_warning(
                "Permission denied: teacher does not own bank",
                teacher_id=teacher_id,
                bank_id=bank_id,
                resource_type="bank"
            )

    return bank is not None


def teacher_owns_class(db: Session, teacher_id: int, class_id: int) -> bool:
    """检查班级是否属于该教师，管理员可以查看所有班级"""
    if is_admin(db, teacher_id):
        return True
    cls = db.query(ClassGroup).filter(
        ClassGroup.id == class_id,
        ClassGroup.created_by == teacher_id,
    ).first()

    if cls is None:
        # 只在班级存在但不属于该教师时记录权限拒绝
        class_exists = db.query(ClassGroup).filter(ClassGroup.id == class_id).first() is not None
        if class_exists:
            log_warning(
                "Permission denied: teacher does not own class",
                teacher_id=teacher_id,
                class_id=class_id,
                resource_type="class"
            )

    return cls is not None


def teacher_owns_question(db: Session, teacher_id: int, question_id: int) -> bool:
    """检查题目是否属于该教师，管理员可以查看所有题目"""
    if is_admin(db, teacher_id):
        return True
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.created_by == teacher_id,
    ).first()

    if question is None:
        # 只在题目存在但不属于该教师时记录权限拒绝
        question_exists = db.query(Question).filter(Question.id == question_id).first() is not None
        if question_exists:
            log_warning(
                "Permission denied: teacher does not own question",
                teacher_id=teacher_id,
                question_id=question_id,
                resource_type="question"
            )

    return question is not None
