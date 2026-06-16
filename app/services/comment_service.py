"""批注服务"""
from sqlalchemy.orm import Session
from app.models import QuestionComment

class CommentService:
    def create_comment(self, db: Session, teacher_id: int, student_id: int,
                       question_id: int, comment_text: str, assignment_id: int = None):
        c = QuestionComment(teacher_id=teacher_id, student_id=student_id,
                           question_id=question_id, comment_text=comment_text,
                           assignment_id=assignment_id)
        db.add(c); db.commit(); db.refresh(c)
        return c

    def get_comments_for_student_question(self, db: Session, student_id: int, question_id: int):
        return db.query(QuestionComment).filter(
            QuestionComment.student_id == student_id,
            QuestionComment.question_id == question_id,
        ).order_by(QuestionComment.created_at.desc()).all()

comment_service = CommentService()
