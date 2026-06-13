from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, Integer
from typing import Annotated

from app.database import get_db
from app.models import Question, Record, User, QuestionBank, ClassGroup, ClassMember, SUBJECTS, SEMESTERS, Feedback
from app.auth import get_current_user, get_current_user_info
from app.security import validate_csrf_async, sanitize_input

router = APIRouter()


@router.get("/")
def index(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = get_current_user(request)
    logged_in = user_id is not None
    role = ""
    display_name = ""
    if logged_in:
        user, role, display_name = get_current_user_info(request, db)

    if logged_in and role == "admin":
        return RedirectResponse(url="/platform/dashboard", status_code=303)

    if logged_in and role == "teacher":
        return RedirectResponse(url="/teacher/questions", status_code=303)

    if logged_in and role == "student":
        return RedirectResponse(url="/student/dashboard", status_code=303)

    total_questions = db.query(Question).count()

    stats = {}
    if logged_in and role == "student":
        total = db.query(Record).filter(Record.user_id == user_id).count()
        correct = (
            db.query(Record)
            .filter(Record.user_id == user_id, Record.is_correct == True)
            .count()
        )
        stats = {
            "total": total,
            "correct": correct,
            "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        }

    question_counts = {}
    for s in SUBJECTS:
        count = db.query(Question).filter(Question.subject == s).count()
        if count > 0:
            question_counts[s] = count

    return request.app.state.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "logged_in": logged_in,
            "role": role,
            "display_name": display_name,
            "total_questions": total_questions,
            "stats": stats,
            "question_counts": question_counts,
            "subjects": SUBJECTS,
        },
    )


@router.get("/browse")
def browse(
    request: Request,
    subject: str = "",
    semester: str = "",
    chapter: str = "",
    bank_id: int = 0,
    access_code_input: str = "",
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = get_current_user(request)
    logged_in = user_id is not None

    subject_counts = {}
    subject_rows = (
        db.query(Question.subject, sa_func.count(Question.id))
        .group_by(Question.subject)
        .all()
    )
    for s, c in subject_rows:
        subject_counts[s] = c

    semester_counts = {}
    chapters = []
    chapter_counts = {}
    questions = []
    banks = []

    teacher_banks = []
    if logged_in and user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "student":
            all_teacher_banks = db.query(QuestionBank).filter(QuestionBank.created_by != None).order_by(QuestionBank.name).all()
            student_class_ids = [c.class_id for c in db.query(ClassMember).filter(ClassMember.user_id == user_id).all()]
            unlocked_bank_ids = request.session.get("unlocked_banks", [])
            for b in all_teacher_banks:
                if b.visibility == "public":
                    q_count = db.query(Question).filter(Question.bank_id == b.id).count()
                    creator = db.query(User).filter(User.id == b.created_by).first()
                    teacher_banks.append({"id": b.id, "name": b.name, "subject": b.subject, "visibility": "public", "q_count": q_count, "creator": creator})
                elif b.visibility == "private":
                    bank_creator = db.query(User).filter(User.id == b.created_by).first()
                    if bank_creator:
                        creator_class_ids = [c.id for c in db.query(ClassGroup).filter(ClassGroup.created_by == bank_creator.id).all()]
                        if set(student_class_ids) & set(creator_class_ids):
                            q_count = db.query(Question).filter(Question.bank_id == b.id).count()
                            teacher_banks.append({"id": b.id, "name": b.name, "subject": b.subject, "visibility": "private", "q_count": q_count, "creator": bank_creator})
                elif b.visibility == "code":
                    if b.id in unlocked_bank_ids:
                        q_count = db.query(Question).filter(Question.bank_id == b.id).count()
                        creator = db.query(User).filter(User.id == b.created_by).first()
                        teacher_banks.append({"id": b.id, "name": b.name, "subject": b.subject, "visibility": "code", "q_count": q_count, "creator": creator})

            if access_code_input:
                matched = db.query(QuestionBank).filter(QuestionBank.visibility == "code", QuestionBank.access_code == access_code_input).first()
                if matched and matched.id not in unlocked_bank_ids:
                    unlocked_bank_ids.append(matched.id)
                    request.session["unlocked_banks"] = unlocked_bank_ids
                    q_count = db.query(Question).filter(Question.bank_id == matched.id).count()
                    creator = db.query(User).filter(User.id == matched.created_by).first()
                    teacher_banks.append({"id": matched.id, "name": matched.name, "subject": matched.subject, "visibility": "code", "q_count": q_count, "creator": creator})

    if subject:
        sem_rows = (
            db.query(Question.semester, sa_func.count(Question.id))
            .filter(Question.subject == subject)
            .group_by(Question.semester)
            .all()
        )
        for sem, cnt in sem_rows:
            label = sem if sem else "未分类"
            semester_counts[label] = cnt

        bank_list = db.query(QuestionBank).filter(
            QuestionBank.subject == subject,
            (QuestionBank.visibility == "public") | (QuestionBank.visibility == None) | (QuestionBank.visibility == "")
        ).order_by(QuestionBank.name).all()
        bank_ids = [b.id for b in bank_list]
        bank_count_rows = (
            db.query(Question.bank_id, sa_func.count(Question.id))
            .filter(Question.bank_id.in_(bank_ids))
            .group_by(Question.bank_id)
            .all()
        )
        bank_count_map = {bid: cnt for bid, cnt in bank_count_rows}
        banks = [{"id": b.id, "name": b.name, "bank_type": b.bank_type, "q_count": bank_count_map.get(b.id, 0)} for b in bank_list]

        if semester:
            chap_rows = (
                db.query(Question.chapter, sa_func.count(Question.id))
                .filter(Question.subject == subject, Question.semester == (semester if semester != "未分类" else ""))
                .group_by(Question.chapter)
                .all()
            )
            for ch, cnt in chap_rows:
                if ch:
                    chapters.append(ch)
                    chapter_counts[ch] = cnt

            if chapter:
                questions = (
                    db.query(Question)
                    .filter(
                        Question.subject == subject,
                        Question.semester == (semester if semester != "未分类" else ""),
                        Question.chapter == chapter,
                    )
                    .order_by(Question.difficulty, Question.id)
                    .all()
                )
            else:
                questions = (
                    db.query(Question)
                    .filter(
                        Question.subject == subject,
                        Question.semester == (semester if semester != "未分类" else ""),
                    )
                    .order_by(Question.difficulty, Question.id)
                    .all()
                )
        else:
            chap_rows = (
                db.query(Question.chapter, sa_func.count(Question.id))
                .filter(Question.subject == subject)
                .group_by(Question.chapter)
                .all()
            )
            for ch, cnt in chap_rows:
                if ch:
                    chapters.append(ch)
                    chapter_counts[ch] = cnt

    if bank_id:
        questions = questions.filter(Question.bank_id == bank_id) if hasattr(questions, 'filter') else [q for q in questions if q.bank_id == bank_id]

    return request.app.state.templates.TemplateResponse(
        "browse.html",
        {
            "request": request,
            "logged_in": logged_in,
            "subject": subject,
            "semester": semester,
            "chapter": chapter,
            "subject_counts": subject_counts,
            "semester_counts": semester_counts,
            "chapters": chapters,
            "chapter_counts": chapter_counts,
            "questions": questions,
            "subjects": SUBJECTS,
            "semesters": SEMESTERS,
            "banks": banks,
            "bank_id": bank_id,
            "teacher_banks": teacher_banks,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.get("/leaderboard")
def leaderboard(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = get_current_user(request)
    logged_in = user_id is not None

    rankings_data = (
        db.query(
            User.id,
            User.username,
            User.display_name,
            sa_func.count(Record.id).label("total"),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)).label("correct"),
        )
        .outerjoin(Record, Record.user_id == User.id)
        .filter(User.role == "student", User.is_guest == False)
        .group_by(User.id)
        .having(sa_func.count(Record.id) > 0)
        .all()
    )
    rankings = [
        {
            "username": r.username,
            "display_name": r.display_name,
            "total": r.total,
            "correct": int(r.correct or 0),
            "accuracy": round((r.correct or 0) / r.total * 100, 1) if r.total > 0 else 0,
        }
        for r in rankings_data
    ]
    rankings.sort(key=lambda x: (-x["correct"], -x["accuracy"]))

    return request.app.state.templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "logged_in": logged_in, "rankings": rankings},
    )


@router.get("/help")
def help_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = get_current_user(request)
    logged_in = user_id is not None
    role = ""
    if logged_in:
        _, role, _ = get_current_user_info(request, db)
    return request.app.state.templates.TemplateResponse(
        "help.html",
        {"request": request, "logged_in": logged_in, "role": role},
    )


@router.post("/feedback")
async def submit_feedback(request: Request, db: Annotated[Session, Depends(get_db)]):
    await validate_csrf_async(request)
    form = await request.form()
    content = sanitize_input(form.get("content", ""), max_length=2000)
    page_path = sanitize_input(form.get("page_path", ""), max_length=500)
    if not content:
        return JSONResponse({"ok": False, "error": "请输入反馈内容"}, status_code=400)
    user_id = get_current_user(request)
    role = ""
    if user_id:
        user, role, _ = get_current_user_info(request, db)
    fb = Feedback(user_id=user_id, role=role, page_path=page_path, content=content)
    db.add(fb)
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/browse/unlock-bank")
async def unlock_bank(request: Request, db: Annotated[Session, Depends(get_db)]):
    await validate_csrf_async(request)
    form = await request.form()
    access_code = sanitize_input(form.get("access_code", "").strip(), max_length=50)
    if not access_code:
        return RedirectResponse(url="/browse", status_code=303)
    return RedirectResponse(url=f"/browse?access_code_input={access_code}", status_code=303)
