from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class RecordBase(BaseModel):
    question_id: int
    user_answer: str
    is_correct: bool


class RecordCreate(RecordBase):
    pass


class RecordResponse(RecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime


class RecordStatsResponse(BaseModel):
    total_count: int
    correct_count: int
    accuracy: float
    today_count: int
