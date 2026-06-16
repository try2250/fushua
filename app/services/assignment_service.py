from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Assignment, AssignmentRecord, Question, Record, ClassMember
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from typing import List, Optional
from datetime import datetime
import json


class AssignmentService:
    def get_assignments(
        self,
        db: Session,
        user_id: int,
        role: str,
        class_id: Optional[int] = None
    ) -> List[Assignment]:
        """获取作业列表"""
        query = db.query(Assignment)

        if role == "teacher":
            query = query.filter(Assignment.created_by == user_id)
        elif role == "student":
            if class_id:
                query = query.filter(Assignment.class_id == class_id)

        if class_id and role == "teacher":
            query = query.filter(Assignment.class_id == class_id)

        return query.order_by(Assignment.created_at.desc()).all()

    def create_assignment(self, db: Session, assignment_data: AssignmentCreate, user_id: int) -> Assignment:
        """创建作业"""
        new_assignment = Assignment(
            **assignment_data.model_dump(),
            created_by=user_id
        )
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        return new_assignment

    def get_assignment_by_id(self, db: Session, assignment_id: int) -> Optional[Assignment]:
        """获取作业详情"""
        return db.query(Assignment).filter(Assignment.id == assignment_id).first()

    def update_assignment(
        self,
        db: Session,
        assignment_id: int,
        assignment_data: AssignmentUpdate
    ) -> Optional[Assignment]:
        """更新作业"""
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            return None

        update_data = assignment_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(assignment, key, value)

        db.commit()
        db.refresh(assignment)
        return assignment

    def delete_assignment(self, db: Session, assignment_id: int) -> bool:
        """删除作业"""
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            return False
        db.delete(assignment)
        db.commit()
        return True

    def submit_assignment(self, db: Session, assignment_id: int, user_id: int) -> AssignmentRecord:
        """提交作业"""
        existing_record = db.query(AssignmentRecord).filter(
            AssignmentRecord.assignment_id == assignment_id,
            AssignmentRecord.user_id == user_id
        ).first()

        if existing_record:
            existing_record.completed = True
            existing_record.completed_at = datetime.now()
            db.commit()
            db.refresh(existing_record)
            return existing_record

        new_record = AssignmentRecord(
            assignment_id=assignment_id,
            user_id=user_id,
            completed=True,
            completed_at=datetime.now()
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record

    def get_assignment_records(self, db: Session, assignment_id: int) -> List[AssignmentRecord]:
        """获取作业提交记录"""
        return db.query(AssignmentRecord).filter(
            AssignmentRecord.assignment_id == assignment_id
        ).all()

    def get_user_assignment_record(
        self,
        db: Session,
        assignment_id: int,
        user_id: int
    ) -> Optional[AssignmentRecord]:
        """获取用户的作业记录"""
        return db.query(AssignmentRecord).filter(
            AssignmentRecord.assignment_id == assignment_id,
            AssignmentRecord.user_id == user_id
        ).first()

    def get_assignments_for_tenant(
        self, db: Session, tenant_id: int, class_id: Optional[int] = None,
    ) -> List[Assignment]:
        from app.models import Assignment
        query = db.query(Assignment).filter(Assignment.created_by == tenant_id)
        if class_id is not None:
            query = query.filter(Assignment.class_id == class_id)
        return query.order_by(Assignment.created_at.desc()).all()

    def get_assignment_by_id_for_tenant(
        self, db: Session, tenant_id: int, assignment_id: int,
    ) -> Optional[Assignment]:
        from app.models import Assignment
        return db.query(Assignment).filter(
            Assignment.id == assignment_id,
            Assignment.created_by == tenant_id,
        ).first()


assignment_service = AssignmentService()


def get_assignment_stats(db: Session, assignment_id: int, teacher_id: int) -> dict:
    """实时 SQL 聚合班级作业统计数据。"""
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.created_by == teacher_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="作业不存在")

    total_students = db.query(ClassMember).filter(
        ClassMember.class_id == assignment.class_id
    ).count()

    submitted_records = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment_id
    ).all()
    submitted_count = len(submitted_records)
    completion_rate = submitted_count / total_students if total_students > 0 else 0
    avg_score = sum(r.score or 0 for r in submitted_records) / submitted_count if submitted_count else 0

    question_ids = json.loads(assignment.question_ids.replace("'", '"')) if assignment.question_ids else []
    question_stats = []
    for qid in question_ids:
        q = db.query(Question).filter(Question.id == qid).first()
        records = db.query(Record).filter(Record.question_id == qid).all()
        correct = sum(1 for r in records if r.is_correct)
        question_stats.append({
            "question_id": qid,
            "question_content": q.content if q else "?",
            "correct_count": correct,
            "total_count": len(records),
            "correct_rate": round(correct / len(records), 2) if records else 0,
        })

    return {
        "assignment_id": assignment_id,
        "total_students": total_students,
        "submitted_count": submitted_count,
        "completion_rate": round(completion_rate, 2),
        "average_score": round(avg_score, 1),
        "max_score": len(question_ids),
        "question_stats": question_stats,
    }
