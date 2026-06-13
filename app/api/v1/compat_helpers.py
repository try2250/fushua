import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Assignment, AssignmentRecord, Question, Record, User
from app.services.record_service import record_service


def question_to_miniprogram_dict(question: Question) -> dict:
    return {
        "id": question.id,
        "subject": question.subject,
        "semester": question.semester,
        "chapter": question.chapter,
        "difficulty": question.difficulty,
        "q_type": question.q_type,
        "content": question.content,
        "option_a": question.option_a,
        "option_b": question.option_b,
        "option_c": question.option_c,
        "option_d": question.option_d,
        "answer": question.answer,
        "correct_answer": question.answer,
        "explanation": question.explanation,
        "image_url": question.image_url,
        "bank_id": question.bank_id,
        "created_by": question.created_by,
        "created_at": question.created_at,
    }


def record_to_miniprogram_dict(record: Record) -> dict:
    data = {
        "id": record.id,
        "user_id": record.user_id,
        "question_id": record.question_id,
        "user_answer": record.user_answer,
        "is_correct": record.is_correct,
        "created_at": record.created_at,
        "updated_at": record.created_at,
    }
    if record.question:
        data["question"] = question_to_miniprogram_dict(record.question)
    return data


def parse_assignment_question_ids(raw: str) -> list[int]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [int(item) for item in parsed]
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


def assignment_to_miniprogram_dict(db: Session, assignment: Assignment, user_id: int) -> dict:
    question_ids = parse_assignment_question_ids(assignment.question_ids)
    questions = []
    if question_ids:
        question_map = {
            question.id: question
            for question in db.query(Question).filter(Question.id.in_(question_ids)).all()
        }
        questions = [
            question_to_miniprogram_dict(question_map[question_id])
            for question_id in question_ids
            if question_id in question_map
        ]

    record = db.query(AssignmentRecord).filter(
        AssignmentRecord.assignment_id == assignment.id,
        AssignmentRecord.user_id == user_id,
    ).first()

    return {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "question_ids": assignment.question_ids,
        "deadline": assignment.deadline,
        "class_id": assignment.class_id,
        "created_by": assignment.created_by,
        "created_at": assignment.created_at,
        "questions": questions,
        "status": "completed" if record and record.completed else "pending",
        "completed": bool(record and record.completed),
    }


def user_stats_for_miniprogram(db: Session, user: User) -> dict:
    stats = record_service.get_stats(db, user.id)
    total_assignments = db.query(Assignment).count() if user.role == "student" else db.query(Assignment).filter(
        Assignment.created_by == user.id
    ).count()
    completed_assignments = db.query(AssignmentRecord).filter(
        AssignmentRecord.user_id == user.id,
        AssignmentRecord.completed == True,
    ).count()
    return {
        "total_questions": stats["total_count"],
        "correct_questions": stats["correct_count"],
        "correct_rate": stats["accuracy"],
        "today_questions": stats["today_count"],
        "total_assignments": total_assignments,
        "completed_assignments": completed_assignments,
    }
