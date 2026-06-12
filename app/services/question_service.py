from sqlalchemy.orm import Session
from app.models import Question
from app.schemas.question import QuestionCreate, QuestionUpdate
from typing import List, Optional
import random


class QuestionService:
    def get_questions(
        self,
        db: Session,
        subject: Optional[str] = None,
        semester: Optional[str] = None,
        chapter: Optional[str] = None,
        q_type: Optional[str] = None,
        difficulty: Optional[int] = None,
        bank_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Question]:
        """获取题目列表（支持筛选）"""
        query = db.query(Question)

        if subject:
            query = query.filter(Question.subject == subject)
        if semester:
            query = query.filter(Question.semester == semester)
        if chapter:
            query = query.filter(Question.chapter == chapter)
        if q_type:
            query = query.filter(Question.q_type == q_type)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if bank_id:
            query = query.filter(Question.bank_id == bank_id)

        return query.offset(offset).limit(limit).all()

    def create_question(self, db: Session, question_data: QuestionCreate, user_id: int) -> Question:
        """创建题目"""
        new_question = Question(
            **question_data.model_dump(),
            created_by=user_id
        )
        db.add(new_question)
        db.commit()
        db.refresh(new_question)
        return new_question

    def get_question_by_id(self, db: Session, question_id: int) -> Optional[Question]:
        """获取题目详情"""
        return db.query(Question).filter(Question.id == question_id).first()

    def update_question(self, db: Session, question_id: int, question_data: QuestionUpdate) -> Optional[Question]:
        """更新题目"""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return None

        update_data = question_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(question, key, value)

        db.commit()
        db.refresh(question)
        return question

    def delete_question(self, db: Session, question_id: int) -> bool:
        """删除题目"""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False
        db.delete(question)
        db.commit()
        return True

    def get_random_questions(
        self,
        db: Session,
        subject: Optional[str] = None,
        semester: Optional[str] = None,
        chapter: Optional[str] = None,
        count: int = 10
    ) -> List[Question]:
        """随机获取题目（刷题用）"""
        query = db.query(Question)

        if subject:
            query = query.filter(Question.subject == subject)
        if semester:
            query = query.filter(Question.semester == semester)
        if chapter:
            query = query.filter(Question.chapter == chapter)

        all_questions = query.all()

        if len(all_questions) <= count:
            return all_questions

        return random.sample(all_questions, count)

    def get_questions_for_tenant(
        self, db, tenant_id: int,
        subject=None, semester=None, chapter=None,
        q_type=None, difficulty=None, bank_id=None,
        limit: int = 20, offset: int = 0,
    ):
        from app.models import Question
        query = db.query(Question).filter(Question.created_by == tenant_id)
        if subject:
            query = query.filter(Question.subject == subject)
        if semester:
            query = query.filter(Question.semester == semester)
        if chapter:
            query = query.filter(Question.chapter == chapter)
        if q_type:
            query = query.filter(Question.q_type == q_type)
        if difficulty is not None:
            query = query.filter(Question.difficulty == difficulty)
        if bank_id is not None:
            query = query.filter(Question.bank_id == bank_id)
        return query.offset(offset).limit(limit).all()

    def get_question_by_id_for_tenant(self, db, tenant_id: int, question_id: int):
        from app.models import Question
        return db.query(Question).filter(
            Question.id == question_id,
            Question.created_by == tenant_id,
        ).first()


question_service = QuestionService()
