from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Union
from datetime import datetime


class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = ""
    question_ids: str
    deadline: Optional[datetime] = None
    class_id: Optional[int] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    question_ids: Optional[str] = None
    deadline: Optional[datetime] = None
    class_id: Optional[int] = None


class AssignmentResponse(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    created_at: datetime


class AssignmentSubmitRequest(BaseModel):
    answers: Union[dict, list]


class AssignmentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    user_id: int
    completed: bool
    completed_at: Optional[datetime] = None
