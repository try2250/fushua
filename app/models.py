import json
import bcrypt
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base

QUESTION_TYPES = {"choice": "选择题", "multi_choice": "多选题", "fill": "填空题", "judge": "判断题"}

SEMESTERS = [
    "七年级上册", "七年级下册",
    "八年级上册", "八年级下册",
    "九年级上册", "九年级下册",
]

SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]

BUILTIN_FIELDS = ["subject", "semester", "chapter", "q_type", "difficulty", "content", "option_a", "option_b", "option_c", "option_d", "answer", "explanation"]

FIELD_TYPE_CHOICES = ["text", "select", "number"]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(10), nullable=False, default="student")
    display_name = Column(String(100), default="")
    created_at = Column(DateTime, server_default=func.now())

    join_mode = Column(String(20), default="")
    is_guest = Column(Boolean, default=False)
    guest_expires_at = Column(DateTime, nullable=True)
    class_id = Column(Integer, nullable=True, index=True)
    is_admin = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    force_password_change = Column(Boolean, default=False)

    records = relationship("Record", back_populates="user")

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), stored_hash.encode())
        except Exception:
            return False


class FieldConfig(Base):
    __tablename__ = "field_configs"

    id = Column(Integer, primary_key=True, index=True)
    field_key = Column(String(50), unique=True, nullable=False, index=True)
    field_label = Column(String(100), nullable=False)
    field_type = Column(String(20), nullable=False, default="text")
    required = Column(Boolean, default=False)
    visible = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    options = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())

    @property
    def options_list(self):
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except (json.JSONDecodeError, TypeError):
            return [o.strip() for o in self.options.split(",") if o.strip()]


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(20), nullable=False)
    semester = Column(String(20), default="")
    chapter = Column(String(100), default="")
    difficulty = Column(Integer, default=1)
    q_type = Column(String(10), nullable=False, default="choice")
    content = Column(Text, nullable=False)
    option_a = Column(String(500), default="")
    option_b = Column(String(500), default="")
    option_c = Column(String(500), default="")
    option_d = Column(String(500), default="")
    answer = Column(String(200), nullable=False)
    explanation = Column(Text, default="")
    image_url = Column(String(500), default="")
    extra_data = Column(Text, default="{}")
    bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    records = relationship("Record", back_populates="question")

    __table_args__ = (
        Index("ix_questions_subject_semester", "subject", "semester"),
        Index("ix_questions_subject_chapter", "subject", "chapter"),
    )

    @property
    def type_label(self):
        return QUESTION_TYPES.get(self.q_type, "未知")

    @property
    def extra(self):
        try:
            return json.loads(self.extra_data) if self.extra_data else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @extra.setter
    def extra(self, value):
        self.extra_data = json.dumps(value, ensure_ascii=False)

    def get_extra_field(self, key, default=""):
        return self.extra.get(key, default)

    def set_extra_field(self, key, value):
        data = self.extra
        data[key] = value
        self.extra_data = json.dumps(data, ensure_ascii=False)


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    user_answer = Column(String(200), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="records")
    question = relationship("Question", back_populates="records")

    __table_args__ = (
        Index("ix_records_user_created", "user_id", "created_at"),
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_favorite_user_question"),
    )


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(20), nullable=False)
    semester = Column(String(20), default="")
    daily_goal = Column(Integer, default=10)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())


class ClassMember(Base):
    __tablename__ = "class_members"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("class_id", "user_id", name="uq_classmember_class_user"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class QuestionBank(Base):
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    subject = Column(String(20), nullable=False)
    semester = Column(String(20), default="")
    description = Column(Text, default="")
    bank_type = Column(String(20), default="custom")
    visibility = Column(String(20), default="public")
    access_code = Column(String(50), default="")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_question_banks_subject", "subject"),
    )


class MasteryRecord(Base):
    __tablename__ = "mastery_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    status = Column(String(20), default="unmastered")
    consecutive_correct = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_mastery_user_question"),
    )


class SiteConfig(Base):
    __tablename__ = "site_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    question_ids = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    deadline = Column(DateTime, nullable=True)
    class_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    records = relationship("AssignmentRecord", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentRecord(Base):
    __tablename__ = "assignment_records"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    assignment = relationship("Assignment", back_populates="records")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    role = Column(String(10), default="")
    page_path = Column(String(500), default="")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50), default="")
    target_id = Column(Integer, nullable=True)
    detail = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())


class ClassJoinRequest(Base):
    __tablename__ = "class_join_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False, index=True)
    display_name = Column(String(100), default="")
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "class_id", name="uq_join_request_user_class"),
    )


class AccountRecoveryRequest(Base):
    __tablename__ = "account_recovery_requests"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=True)
    display_name = Column(String(100), default="")
    status = Column(String(20), default="pending")
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    new_password_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
