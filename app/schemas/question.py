from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class QuestionBase(BaseModel):
    subject: str
    semester: Optional[str] = ""
    chapter: Optional[str] = ""
    difficulty: Optional[int] = 1
    q_type: str
    content: str
    option_a: Optional[str] = ""
    option_b: Optional[str] = ""
    option_c: Optional[str] = ""
    option_d: Optional[str] = ""
    answer: str
    explanation: Optional[str] = ""
    image_url: Optional[str] = ""
    bank_id: Optional[int] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    subject: Optional[str] = None
    semester: Optional[str] = None
    chapter: Optional[str] = None
    difficulty: Optional[int] = None
    q_type: Optional[str] = None
    content: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    image_url: Optional[str] = None
    bank_id: Optional[int] = None


class QuestionResponse(QuestionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    created_at: datetime


class QuestionListQuery(BaseModel):
    subject: Optional[str] = None
    semester: Optional[str] = None
    chapter: Optional[str] = None
    q_type: Optional[str] = None
    difficulty: Optional[int] = None
    bank_id: Optional[int] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0
