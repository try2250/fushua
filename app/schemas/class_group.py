from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ClassGroupBase(BaseModel):
    name: str


class ClassGroupCreate(ClassGroupBase):
    pass


class ClassGroupUpdate(BaseModel):
    name: Optional[str] = None


class ClassMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    display_name: str
    role: str
    joined_at: datetime


class ClassGroupResponse(ClassGroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    created_at: datetime
    member_count: Optional[int] = 0


class ClassGroupDetailResponse(ClassGroupResponse):
    members: List[ClassMemberResponse] = []
