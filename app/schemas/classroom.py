"""
课堂管理相关的 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime


# ========== 课堂会话 ==========

class ClassroomSessionCreate(BaseModel):
    """创建课堂会话请求"""
    class_id: int = Field(..., description="班级 ID")
    title: str = Field(..., min_length=1, max_length=200, description="课堂标题")
    mode: str = Field(default="normal", description="课堂模式: normal/streak/self_select")


class ClassroomSessionResponse(BaseModel):
    """课堂会话响应"""
    id: int
    class_id: int
    teacher_id: int
    title: str
    mode: str
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 课堂抽取记录 ==========

class ClassroomDrawCreate(BaseModel):
    """创建课堂抽取记录请求"""
    student_id: int = Field(..., description="学生 ID")
    question_id: Optional[int] = Field(None, description="题目 ID（可选）")
    result: str = Field(..., description="结果: correct/wrong/skip/manual")
    score_delta: int = Field(default=0, description="积分变化")
    note: str = Field(default="", description="备注")


class ClassroomDrawResponse(BaseModel):
    """课堂抽取记录响应"""
    id: int
    session_id: int
    class_id: int
    student_id: int
    question_id: Optional[int]
    result: str
    score_delta: int
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 课堂学生 ==========

class ClassroomStudentResponse(BaseModel):
    """课堂学生响应"""
    id: int
    username: str
    display_name: str
    phone: Optional[str]

    class Config:
        from_attributes = True


# ========== 课堂班级 ==========

class ClassroomClassResponse(BaseModel):
    """课堂班级响应"""
    id: int
    name: str
    created_at: datetime
    student_count: int = 0

    class Config:
        from_attributes = True


# ========== 课堂题库 ==========

class ClassroomQuestionBankResponse(BaseModel):
    """课堂题库响应"""
    id: int
    name: str
    subject: Optional[str]
    question_count: int = 0

    class Config:
        from_attributes = True


# ========== 课堂题目 ==========

class ClassroomQuestionResponse(BaseModel):
    """课堂题目响应"""
    id: int
    subject: str
    chapter: str
    difficulty: int
    q_type: str
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    answer: str
    explanation: str

    class Config:
        from_attributes = True


# ========== 结束课堂 ==========

class ClassroomSessionFinish(BaseModel):
    """结束课堂会话请求"""
    session_id: int = Field(..., description="会话 ID")


# ========== 课堂 Bootstrap ==========

class ClassroomBootstrapResponse(BaseModel):
    """课堂初始化响应"""
    classes: List[ClassroomClassResponse]
    active_session: Optional[ClassroomSessionResponse] = None
    local_storage_business_keys: List[str] = []


# ========== 课堂会话状态 ==========

class ClassroomSessionStateUpdate(BaseModel):
    """课堂会话状态更新请求"""
    state: Dict[str, Any]
    version: int = Field(default=1, ge=1)


class ClassroomSessionStateResponse(BaseModel):
    """课堂会话状态响应"""
    session_id: int
    state: Dict[str, Any]
    version: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 课堂积分与统计 ==========

class ClassroomScoreboardItem(BaseModel):
    """课堂积分榜单项"""
    student_id: int
    student_name: str
    score: int
    draw_count: int
    correct_count: int
    wrong_count: int


class ClassroomSessionSummary(BaseModel):
    """课堂会话摘要"""
    session_id: int
    total_draws: int
    correct_count: int
    wrong_count: int
    skip_count: int
    scoreboard: List[ClassroomScoreboardItem]
