from sqlalchemy.orm import Session
from app.models import Assignment, AssignmentRecord, Question
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


assignment_service = AssignmentService()
