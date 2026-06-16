"""批注 API"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.models import User, QuestionComment
from app.services.comment_service import comment_service
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/comments", tags=["批注"])

class CreateCommentRequest(BaseModel):
    student_id: int
    question_id: int
    comment_text: str
    assignment_id: Optional[int] = None

@router.post("", response_model=ResponseModel[dict])
def create_comment(req: CreateCommentRequest, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user),
                   tenant: TenantContext = Depends(get_tenant_context)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="仅教师可批注")
    c = comment_service.create_comment(db, teacher_id=current_user.id, student_id=req.student_id,
                                       question_id=req.question_id, comment_text=req.comment_text,
                                       assignment_id=req.assignment_id)
    return ResponseModel(data={"id": c.id})

@router.get("", response_model=ResponseModel[list])
def get_comments(student_id: int = Query(...), question_id: int = Query(...),
                 db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
                 tenant: TenantContext = Depends(get_tenant_context)):
    comments = comment_service.get_comments_for_student_question(db, student_id, question_id)
    return ResponseModel(data=[{"id": c.id, "teacher_id": c.teacher_id, "comment_text": c.comment_text,
                                "created_at": str(c.created_at)} for c in comments])
