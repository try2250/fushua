import json
import bcrypt
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, UniqueConstraint, Index
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
    is_disabled = Column(Boolean, default=False)
    force_password_change = Column(Boolean, default=False)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    openid = Column(String(100), unique=True, nullable=True, index=True)
    is_phone_verified = Column(Boolean, default=False)
    avatar_url = Column(String(500), nullable=True)
    nickname = Column(String(100), nullable=True)
    wechat_unionid = Column(String(100), nullable=True)

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
    q_type = Column(String(50), nullable=False, default="choice")
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
    def correct_answer(self):
        return self.answer

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

    creator = relationship("User", foreign_keys=[created_by])


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

    user = relationship("User", foreign_keys=[user_id])
    class_group = relationship("ClassGroup", foreign_keys=[class_id])

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


class BackupLog(Base):
    __tablename__ = "backup_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    status = Column(String(20), nullable=False, index=True)
    file_path = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    triggered_by = Column(String(50), default="cron")
    duration_seconds = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<BackupLog(id={self.id}, status={self.status}, created_at={self.created_at})>"


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), nullable=False)
    code = Column(String(6), nullable=False)
    purpose = Column(String(20), nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_verification_codes_phone_expires', 'phone', 'expires_at'),
    )


class Announcement(Base):
    """系统公告模型"""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(20), default="info")  # info, warning, success, error
    target_role = Column(String(20), default="all")  # all, student, teacher, admin
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # 数字越大优先级越高
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)

    # 关系
    creator = relationship("User", foreign_keys=[created_by])

    # 索引：优化公告查询性能
    __table_args__ = (
        Index('idx_announcements_active_role_expires', 'is_active', 'target_role', 'expires_at'),
    )


class ClassroomSession(Base):
    """课堂会话模型"""
    __tablename__ = "classroom_sessions"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    mode = Column(String(50), default="normal")  # normal, streak, self_select
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    class_group = relationship("ClassGroup", foreign_keys=[class_id])
    teacher = relationship("User", foreign_keys=[teacher_id])
    draw_records = relationship("ClassroomDrawRecord", back_populates="session")

    # 索引
    __table_args__ = (
        Index('idx_classroom_sessions_teacher_created', 'teacher_id', 'created_at'),
        Index('idx_classroom_sessions_class_created', 'class_id', 'created_at'),
    )


class ClassroomDrawRecord(Base):
    """课堂抽取记录模型"""
    __tablename__ = "classroom_draw_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("classroom_sessions.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    result = Column(String(20), nullable=False)  # correct, wrong, skip, manual
    score_delta = Column(Integer, default=0)  # 积分变化
    note = Column(Text, default="")  # 备注
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    session = relationship("ClassroomSession", back_populates="draw_records")
    class_group = relationship("ClassGroup", foreign_keys=[class_id])
    student = relationship("User", foreign_keys=[student_id])
    question = relationship("Question", foreign_keys=[question_id])

    # 索引
    __table_args__ = (
        Index('idx_classroom_draw_session_created', 'session_id', 'created_at'),
        Index('idx_classroom_draw_student_created', 'student_id', 'created_at'),
    )


class ClassroomQuestionSnapshot(Base):
    """课堂题目快照模型 - 保留课堂当时的题目内容"""
    __tablename__ = "classroom_question_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("classroom_sessions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    content_snapshot = Column(Text, nullable=False)
    answer_snapshot = Column(String(200), nullable=False)
    explanation_snapshot = Column(Text, default="")
    extra_snapshot = Column(Text, default="{}")  # 包含选项等额外信息的 JSON
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    session = relationship("ClassroomSession", foreign_keys=[session_id])
    question = relationship("Question", foreign_keys=[question_id])

    # 索引
    __table_args__ = (
        Index('idx_classroom_snapshot_session_question', 'session_id', 'question_id'),
    )


class ClassroomSessionState(Base):
    """Cloud state for an in-progress classroom session."""
    __tablename__ = "classroom_session_states"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("classroom_sessions.id"), nullable=False, unique=True, index=True)
    state_json = Column(Text, default="{}")
    version = Column(Integer, default=1)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    session = relationship("ClassroomSession", foreign_keys=[session_id])


class ClassroomGroupSet(Base):
    """A saved grouping result for one classroom session."""
    __tablename__ = "classroom_group_sets"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("classroom_sessions.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("ClassroomSession", foreign_keys=[session_id])


class ClassroomGroupMember(Base):
    """Student membership inside a saved classroom group set."""
    __tablename__ = "classroom_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_set_id = Column(Integer, ForeignKey("classroom_group_sets.id"), nullable=False, index=True)
    group_name = Column(String(100), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0)

    group_set = relationship("ClassroomGroupSet", foreign_keys=[group_set_id])
    student = relationship("User", foreign_keys=[student_id])


class PlatformAdmin(Base):
    __tablename__ = "platform_admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), stored_hash.encode())
        except Exception:
            return False


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    question_count = Column(Integer, default=0)
    is_checked = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date_checkin"),)


class UserStreak(Base):
    __tablename__ = "user_streaks"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    last_checkin_date = Column(Date, nullable=True)


class WeeklyScore(Base):
    __tablename__ = "weekly_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)
    score = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("user_id", "class_id", "week_start", name="uq_user_class_week"),)


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))
    description = Column(String(500))
    icon_url = Column(String(500))


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)


class OnboardingState(Base):
    __tablename__ = "onboarding_states"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    step = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)

