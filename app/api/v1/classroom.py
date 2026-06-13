"""
课堂管理 API 接口
提供课堂会话、抽取记录等功能的 RESTful API
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import (
    ClassGroup, ClassMember, User, Question, QuestionBank,
    ClassroomSession, ClassroomDrawRecord, ClassroomQuestionSnapshot,
    ClassroomSessionState, MasteryRecord,
)
from app.schemas.classroom import (
    ClassroomSessionCreate, ClassroomSessionResponse,
    ClassroomDrawCreate, ClassroomDrawResponse,
    ClassroomStudentResponse, ClassroomClassResponse,
    ClassroomQuestionBankResponse, ClassroomQuestionResponse,
    ClassroomBootstrapResponse, ClassroomSessionStateUpdate,
    ClassroomSessionStateResponse,
    ClassroomScoreboardItem, ClassroomSessionSummary,
)
from app.schemas.common import ResponseModel
from app.core.security import verify_token


router = APIRouter(prefix="/classroom", tags=["课堂管理 API"])
optional_bearer = HTTPBearer(auto_error=False)


def get_current_teacher(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    db: Session = Depends(get_db)
) -> User:
    """获取当前教师用户，兼容小程序 Bearer token 和 Web 后台 session。"""
    user_id = None
    if credentials:
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭证")
        user_id = payload.get("user_id")
    else:
        user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user or current_user.is_disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")

    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="仅教师可访问")

    return current_user


@router.get("/classes", response_model=ResponseModel[List[ClassroomClassResponse]])
def get_teacher_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取教师的班级列表"""
    classes = db.query(ClassGroup).filter(
        ClassGroup.created_by == current_user.id
    ).all()

    result = []
    for cls in classes:
        student_count = db.query(ClassMember).filter(
            ClassMember.class_id == cls.id
        ).count()

        result.append(ClassroomClassResponse(
            id=cls.id,
            name=cls.name,
            created_at=cls.created_at,
            student_count=student_count
        ))

    return ResponseModel(data=result)


@router.get("/classes/{class_id}/students", response_model=ResponseModel[List[ClassroomStudentResponse]])
def get_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取班级学生列表"""
    # 验证班级所有权
    cls = db.query(ClassGroup).filter(
        ClassGroup.id == class_id,
        ClassGroup.created_by == current_user.id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 获取学生
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()
    student_ids = [m.user_id for m in members]

    students = db.query(User).filter(User.id.in_(student_ids)).all()

    result = [
        ClassroomStudentResponse(
            id=s.id,
            username=s.username,
            display_name=s.display_name or s.username,
            phone=s.phone
        )
        for s in students
    ]

    return ResponseModel(data=result)


@router.get("/question-banks", response_model=ResponseModel[List[ClassroomQuestionBankResponse]])
def get_teacher_question_banks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取教师的题库列表"""
    banks = db.query(QuestionBank).filter(
        QuestionBank.created_by == current_user.id
    ).all()

    result = []
    for bank in banks:
        question_count = db.query(Question).filter(
            Question.bank_id == bank.id
        ).count()

        result.append(ClassroomQuestionBankResponse(
            id=bank.id,
            name=bank.name,
            subject=bank.subject,
            question_count=question_count
        ))

    return ResponseModel(data=result)


@router.get("/questions", response_model=ResponseModel[List[ClassroomQuestionResponse]])
def get_questions(
    bank_id: int = None,
    subject: str = None,
    chapter: str = None,
    difficulty: int = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取教师的题目列表（用于课堂抽题）"""
    query = db.query(Question).filter(Question.created_by == current_user.id)

    if bank_id:
        query = query.filter(Question.bank_id == bank_id)
    if subject:
        query = query.filter(Question.subject == subject)
    if chapter:
        query = query.filter(Question.chapter == chapter)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    questions = query.limit(limit).all()

    return ResponseModel(data=[ClassroomQuestionResponse.from_orm(q) for q in questions])


@router.post("/sessions", response_model=ResponseModel[ClassroomSessionResponse])
def create_session(
    request: ClassroomSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """创建课堂会话"""
    # 验证班级所有权
    cls = db.query(ClassGroup).filter(
        ClassGroup.id == request.class_id,
        ClassGroup.created_by == current_user.id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 创建会话
    session = ClassroomSession(
        class_id=request.class_id,
        teacher_id=current_user.id,
        title=request.title,
        mode=request.mode
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return ResponseModel(data=ClassroomSessionResponse.from_orm(session))


@router.get("/sessions/{session_id}", response_model=ResponseModel[ClassroomSessionResponse])
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取课堂会话详情"""
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")

    return ResponseModel(data=ClassroomSessionResponse.from_orm(session))


@router.post("/sessions/{session_id}/draws", response_model=ResponseModel[ClassroomDrawResponse])
def create_draw_record(
    session_id: int,
    request: ClassroomDrawCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """创建课堂抽取记录"""
    # 验证会话所有权
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")

    # 如果有题目，创建题目快照
    if request.question_id:
        question = db.query(Question).filter(Question.id == request.question_id).first()
        if question:
            # 检查是否已有快照
            snapshot = db.query(ClassroomQuestionSnapshot).filter(
                ClassroomQuestionSnapshot.session_id == session_id,
                ClassroomQuestionSnapshot.question_id == request.question_id
            ).first()

            if not snapshot:
                import json
                extra_data = {
                    "subject": question.subject,
                    "q_type": question.q_type,
                    "option_a": question.option_a,
                    "option_b": question.option_b,
                    "option_c": question.option_c,
                    "option_d": question.option_d,
                }

                snapshot = ClassroomQuestionSnapshot(
                    session_id=session_id,
                    question_id=question.id,
                    content_snapshot=question.content,
                    answer_snapshot=question.answer,
                    explanation_snapshot=question.explanation,
                    extra_snapshot=json.dumps(extra_data, ensure_ascii=False)
                )
                db.add(snapshot)

    # 创建抽取记录
    draw_record = ClassroomDrawRecord(
        session_id=session_id,
        class_id=session.class_id,
        student_id=request.student_id,
        question_id=request.question_id,
        result=request.result,
        score_delta=request.score_delta,
        note=request.note
    )

    db.add(draw_record)

    # ===== 同步 MasteryRecord（课堂错题与练习打通） =====
    if request.question_id and request.result in ("wrong", "correct"):
        # Upsert: 查找或创建 mastery 记录
        mastery = db.query(MasteryRecord).filter(
            MasteryRecord.user_id == request.student_id,
            MasteryRecord.question_id == request.question_id,
        ).first()

        if not mastery:
            mastery = MasteryRecord(
                user_id=request.student_id,
                question_id=request.question_id,
                status="unmastered",
                consecutive_correct=0,
            )
            db.add(mastery)

        if request.result == "wrong":
            mastery.status = "unmastered"
            mastery.consecutive_correct = 0
        elif request.result == "correct":
            mastery.consecutive_correct += 1
            if mastery.consecutive_correct >= 3:
                mastery.status = "mastered"

    db.commit()
    db.refresh(draw_record)

    return ResponseModel(data=ClassroomDrawResponse.from_orm(draw_record))


@router.get("/sessions/{session_id}/draws", response_model=ResponseModel[List[ClassroomDrawResponse]])
def get_session_draws(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取课堂会话的抽取记录"""
    # 验证会话所有权
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")

    draws = db.query(ClassroomDrawRecord).filter(
        ClassroomDrawRecord.session_id == session_id
    ).order_by(ClassroomDrawRecord.created_at).all()

    return ResponseModel(data=[ClassroomDrawResponse.from_orm(d) for d in draws])


@router.post("/sessions/{session_id}/finish", response_model=ResponseModel[ClassroomSessionResponse])
def finish_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """结束课堂会话"""
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")

    if session.ended_at:
        raise HTTPException(status_code=400, detail="课堂已结束")

    session.ended_at = datetime.now()
    db.commit()
    db.refresh(session)

    return ResponseModel(data=ClassroomSessionResponse.from_orm(session))


# ========== 课堂总结与积分榜 ==========

@router.get("/sessions/{session_id}/summary", response_model=ResponseModel[ClassroomSessionSummary])
def get_session_summary(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """获取课堂会话的统计摘要与积分榜。

    聚合该 session 下所有 DrawRecord，按学生计算：
    - total_draws / correct_count / wrong_count / skip_count
    - scoreboard: 每个学生的得分、答题数、正确/错误数
    """
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")

    draws = db.query(ClassroomDrawRecord).filter(
        ClassroomDrawRecord.session_id == session_id
    ).all()

    total_draws = len(draws)
    correct_count = sum(1 for d in draws if d.result == "correct")
    wrong_count = sum(1 for d in draws if d.result == "wrong")
    skip_count = sum(1 for d in draws if d.result == "skip")
    manual_count = sum(1 for d in draws if d.result == "manual")

    # 按学生聚合
    student_agg = {}
    for d in draws:
        sid = d.student_id
        if sid not in student_agg:
            student_agg[sid] = {"score": 0, "draw_count": 0, "correct": 0, "wrong": 0}
        student_agg[sid]["score"] += d.score_delta
        student_agg[sid]["draw_count"] += 1
        if d.result == "correct":
            student_agg[sid]["correct"] += 1
        elif d.result == "wrong":
            student_agg[sid]["wrong"] += 1

    # 获取学生姓名
    student_ids = list(student_agg.keys())
    users = db.query(User).filter(User.id.in_(student_ids)).all() if student_ids else []
    name_map = {u.id: u.display_name or u.username for u in users}

    scoreboard = sorted([
        ClassroomScoreboardItem(
            student_id=sid,
            student_name=name_map.get(sid, f"学生{sid}"),
            score=agg["score"],
            draw_count=agg["draw_count"],
            correct_count=agg["correct"],
            wrong_count=agg["wrong"],
        )
        for sid, agg in student_agg.items()
    ], key=lambda x: x.score, reverse=True)

    return ResponseModel(data=ClassroomSessionSummary(
        session_id=session_id,
        total_draws=total_draws,
        correct_count=correct_count,
        wrong_count=wrong_count + manual_count,
        skip_count=skip_count,
        scoreboard=scoreboard,
    ))


@router.get("/classes/{class_id}/scoreboard")
def get_class_scoreboard(
    class_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """获取班级在最近 N 天内所有课堂的积分榜（跨 session 聚合）。
    
    统计每位学生在所有课堂中的总得分、总答题数、总正确/错误数。
    即使某学生从未被抽取，也会出现在列表中（分数为 0）。
    """
    cls = db.query(ClassGroup).filter(
        ClassGroup.id == class_id,
        ClassGroup.created_by == current_user.id,
    ).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    from datetime import timezone as _tz
    cutoff = datetime.now(tz=_tz.utc) - timedelta(days=days)

    draws = db.query(ClassroomDrawRecord).join(ClassroomSession).filter(
        ClassroomDrawRecord.class_id == class_id,
        ClassroomDrawRecord.created_at >= cutoff,
        ClassroomSession.teacher_id == current_user.id,
    ).all()

    student_agg: dict = {}
    for d in draws:
        sid = d.student_id
        if sid not in student_agg:
            student_agg[sid] = {"score": 0, "draw_count": 0, "correct": 0, "wrong": 0}
        student_agg[sid]["score"] += d.score_delta
        student_agg[sid]["draw_count"] += 1
        if d.result == "correct":
            student_agg[sid]["correct"] += 1
        elif d.result == "wrong":
            student_agg[sid]["wrong"] += 1

    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()
    all_ids = set(m.user_id for m in members)
    for sid in all_ids:
        if sid not in student_agg:
            student_agg[sid] = {"score": 0, "draw_count": 0, "correct": 0, "wrong": 0}

    users = db.query(User).filter(User.id.in_(list(all_ids))).all() if all_ids else []
    name_map = {u.id: u.display_name or u.username for u in users}

    scoreboard = sorted([
        ClassroomScoreboardItem(
            student_id=sid, student_name=name_map.get(sid, f"学生{sid}"),
            score=agg["score"], draw_count=agg["draw_count"],
            correct_count=agg["correct"], wrong_count=agg["wrong"],
        ) for sid, agg in student_agg.items()
    ], key=lambda x: x.score, reverse=True)

    total_draws = len(draws)
    correct_count = sum(1 for d in draws if d.result == "correct")
    wrong_count = sum(1 for d in draws if d.result in ("wrong", "manual"))
    skip_count = sum(1 for d in draws if d.result == "skip")

    return {
        "class_id": class_id, "days": days,
        "total_draws": total_draws, "correct_count": correct_count,
        "wrong_count": wrong_count, "skip_count": skip_count,
        "total_students": len(all_ids),
        "scoreboard": [s.model_dump() for s in scoreboard],
    }


@router.get("/sessions/{session_id}/wrong-questions")
def get_session_wrong_questions(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """获取课堂中所有学生答错的题目（去重），用于创建针对性练习/作业。

    返回: { session_id, wrong_questions: [{question_id, content, subject, wrong_count}] }
    """
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")

    wrong_draws = db.query(ClassroomDrawRecord).filter(
        ClassroomDrawRecord.session_id == session_id,
        ClassroomDrawRecord.result == "wrong",
    ).all()

    # 按 question_id 聚合
    agg = {}
    for d in wrong_draws:
        if not d.question_id:
            continue
        if d.question_id not in agg:
            agg[d.question_id] = {"count": 0}
        agg[d.question_id]["count"] += 1

    question_ids = list(agg.keys())
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []
    q_map = {q.id: q for q in questions}

    wrong_questions = sorted([
        {
            "question_id": qid,
            "content": q_map[qid].content if qid in q_map else "(题目已删除)",
            "subject": q_map[qid].subject if qid in q_map else "",
            "q_type": q_map[qid].q_type if qid in q_map else "",
            "wrong_count": info["count"],
        }
        for qid, info in agg.items()
    ], key=lambda x: x["wrong_count"], reverse=True)

    return ResponseModel(data={
        "session_id": session_id,
        "total_wrong": len(wrong_draws),
        "distinct_questions": len(wrong_questions),
        "wrong_questions": wrong_questions,
    })


@router.get("/classes/{class_id}/classroom-wrong-questions")
def get_class_classroom_wrong_questions(
    class_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """获取班级在最近 N 天所有课堂中的错题汇总，用于批量创建练习/作业。

    Query params:
        days (int): 统计最近多少天，默认 30 天
    """
    from datetime import timezone
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

    # 查询最近 N 天内该班级所有课堂的答错记录
    wrong_draws = db.query(ClassroomDrawRecord).join(ClassroomSession).filter(
        ClassroomDrawRecord.class_id == class_id,
        ClassroomDrawRecord.result == "wrong",
        ClassroomDrawRecord.created_at >= cutoff,
        ClassroomSession.teacher_id == current_user.id,
    ).all()

    # 按 question_id 聚合
    agg = {}
    for d in wrong_draws:
        if not d.question_id:
            continue
        if d.question_id not in agg:
            agg[d.question_id] = {"count": 0, "student_ids": set()}
        agg[d.question_id]["count"] += 1
        agg[d.question_id]["student_ids"].add(d.student_id)

    question_ids = list(agg.keys())
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []
    q_map = {q.id: q for q in questions}

    wrong_questions = sorted([
        {
            "question_id": qid,
            "content": q_map[qid].content if qid in q_map else "(题目已删除)",
            "subject": q_map[qid].subject if qid in q_map else "",
            "q_type": q_map[qid].q_type if qid in q_map else "",
            "wrong_count": info["count"],
            "affected_students": len(info["student_ids"]),
        }
        for qid, info in agg.items()
    ], key=lambda x: x["wrong_count"], reverse=True)

    return ResponseModel(data={
        "class_id": class_id,
        "days": days,
        "total_wrong_records": len(wrong_draws),
        "distinct_questions": len(wrong_questions),
        "wrong_questions": wrong_questions,
    })


@router.get("/bootstrap", response_model=ResponseModel[ClassroomBootstrapResponse])
def classroom_bootstrap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """教师课堂初始化：返回班级列表、活跃课堂、UI初始状态。"""
    classes = db.query(ClassGroup).filter(
        ClassGroup.created_by == current_user.id
    ).order_by(ClassGroup.created_at.desc()).all()

    class_items = []
    for cls in classes:
        student_count = db.query(ClassMember).filter(ClassMember.class_id == cls.id).count()
        class_items.append(ClassroomClassResponse(
            id=cls.id,
            name=cls.name,
            student_count=student_count,
            created_at=cls.created_at,
        ))

    active_session = db.query(ClassroomSession).filter(
        ClassroomSession.teacher_id == current_user.id,
        ClassroomSession.ended_at == None,
    ).order_by(ClassroomSession.created_at.desc()).first()

    active_session_data = None
    if active_session:
        active_session_data = ClassroomSessionResponse(
            id=active_session.id,
            class_id=active_session.class_id,
            teacher_id=active_session.teacher_id,
            title=active_session.title,
            mode=active_session.mode,
            started_at=active_session.started_at,
            ended_at=active_session.ended_at,
            created_at=active_session.created_at,
        )

    return ResponseModel(data=ClassroomBootstrapResponse(
        classes=class_items,
        active_session=active_session_data,
        local_storage_business_keys=[],
    ))


@router.patch("/sessions/{session_id}/state", response_model=ResponseModel[ClassroomSessionStateResponse])
def save_session_state(
    session_id: int,
    request_data: ClassroomSessionStateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """保存课堂会话的业务状态（当前题目、被抽学生、分组引用等）。"""
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")
    if session.ended_at:
        raise HTTPException(status_code=400, detail="课堂已结束，不能继续保存状态")

    row = db.query(ClassroomSessionState).filter(
        ClassroomSessionState.session_id == session_id
    ).first()
    if not row:
        row = ClassroomSessionState(session_id=session_id)
        db.add(row)

    row.state_json = json.dumps(request_data.state, ensure_ascii=False)
    row.version = request_data.version
    db.commit()
    db.refresh(row)

    return ResponseModel(data=ClassroomSessionStateResponse(
        session_id=session_id,
        state=json.loads(row.state_json or "{}"),
        version=row.version,
        updated_at=row.updated_at,
    ))


@router.get("/sessions/{session_id}/state", response_model=ResponseModel[ClassroomSessionStateResponse])
def get_session_state(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """获取课堂会话的业务状态，支持刷新和换设备恢复。"""
    session = db.query(ClassroomSession).filter(
        ClassroomSession.id == session_id,
        ClassroomSession.teacher_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="课堂会话不存在")

    row = db.query(ClassroomSessionState).filter(
        ClassroomSessionState.session_id == session_id
    ).first()

    if row:
        state_data = json.loads(row.state_json or "{}")
    else:
        state_data = {}

    return ResponseModel(data=ClassroomSessionStateResponse(
        session_id=session_id,
        state=state_data,
        version=row.version if row else 1,
        updated_at=row.updated_at if row else None,
    ))
