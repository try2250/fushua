import random
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func, Integer
from typing import Annotated

from app.database import get_db
from app.models import User, Question, Record, QUESTION_TYPES, Favorite, StudyPlan, Notification, SUBJECTS as MODEL_SUBJECTS, SEMESTERS, MasteryRecord, Assignment, AssignmentRecord
from app.auth import require_login, require_non_guest, get_current_user
from app.security import validate_csrf_async, sanitize_input
from app.utils.validation import parse_int

router = APIRouter(prefix="/student")

SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]


@router.get("/guest-expired")
def guest_expired_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_guest:
        return RedirectResponse(url="/", status_code=303)
    return request.app.state.templates.TemplateResponse(
        "student/guest_expired.html",
        {"request": request},
    )


@router.get("/dashboard")
def dashboard(request: Request, db: Annotated[Session, Depends(get_db)]):
    user_id = require_non_guest(request, db)
    today = date.today()

    assignments = db.query(Assignment).order_by(Assignment.created_at.desc()).all()
    completed_assignment_ids = set(
        r.assignment_id for r in db.query(AssignmentRecord).filter(AssignmentRecord.user_id == user_id).all()
    )
    pending_assignments = [a for a in assignments if a.id not in completed_assignment_ids]

    recommended = _smart_select(user_id, db, count=5)

    wrong_qids = set(
        r[0] for r in db.query(Record.question_id)
        .filter(Record.user_id == user_id, Record.is_correct == False).distinct().all()
    )
    mastered_wrong = set()
    if wrong_qids:
        corrected = set(
            r[0] for r in db.query(Record.question_id)
            .filter(Record.user_id == user_id, Record.question_id.in_(wrong_qids), Record.is_correct == True)
            .distinct().all()
        )
        mastered_wrong = corrected
    unmastered_mistake_count = len(wrong_qids - mastered_wrong)

    today_record_count = db.query(Record).filter(
        Record.user_id == user_id,
        sa_func.date(Record.created_at) == today,
    ).count()

    active_plan = db.query(StudyPlan).filter(StudyPlan.user_id == user_id, StudyPlan.active == True).first()
    daily_goal = active_plan.daily_goal if active_plan else 10
    progress = min(round(today_record_count / daily_goal * 100, 1), 100) if daily_goal > 0 else 0

    return request.app.state.templates.TemplateResponse(
        "student/dashboard.html",
        {
            "request": request,
            "pending_assignments": pending_assignments,
            "recommended": recommended,
            "unmastered_mistake_count": unmastered_mistake_count,
            "today_record_count": today_record_count,
            "daily_goal": daily_goal,
            "progress": progress,
        },
    )


def check_answer(question: Question, user_answer: str) -> bool:
    if question.q_type == "choice":
        return user_answer.strip().upper() == question.answer.strip().upper()
    elif question.q_type == "multi_choice":
        ua = "".join(sorted(user_answer.strip().upper().replace(",", "")))
        ca = "".join(sorted(question.answer.strip().upper().replace(",", "")))
        return ua == ca
    elif question.q_type == "judge":
        return user_answer.strip() == question.answer.strip()
    elif question.q_type == "fill":
        ua = user_answer.strip().replace(" ", "").lower()
        ca = question.answer.strip().replace(" ", "").lower()
        return ua == ca
    return False


def _get_weak_subjects(user_id: int, db: Session) -> list:
    by_subject = (
        db.query(
            Question.subject,
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id)
        .group_by(Question.subject)
        .all()
    )
    weak = []
    for s, t, c in by_subject:
        acc = (c or 0) / t if t > 0 else 0
        if acc < 0.7:
            weak.append((s, acc))
    weak.sort(key=lambda x: x[1])
    return [w[0] for w in weak]


def _smart_select(user_id: int, db: Session, subject: str = "", semester: str = "", chapter: str = "", count: int = 10, mode: str = "smart") -> list:
    query = db.query(Question)
    if subject:
        query = query.filter(Question.subject == subject)
    if semester:
        query = query.filter(Question.semester == semester)
    if chapter:
        query = query.filter(Question.chapter == chapter)

    all_questions = query.all()
    if not all_questions:
        return []

    if mode == "adaptive":
        recent_records = (
            db.query(Record)
            .filter(Record.user_id == user_id)
            .order_by(Record.created_at.desc())
            .limit(10)
            .all()
        )
        if recent_records:
            correct_count = sum(1 for r in recent_records if r.is_correct)
            accuracy = correct_count / len(recent_records)
            if accuracy < 0.4:
                max_difficulty = 1
            elif accuracy < 0.7:
                max_difficulty = 2
            else:
                max_difficulty = 3
        else:
            max_difficulty = 2
        filtered = [q for q in all_questions if q.difficulty <= max_difficulty]
        if not filtered:
            filtered = all_questions
        random.shuffle(filtered)
        return [(q, "难度适配") for q in filtered[:count]]

    n_unmastered = max(1, round(count * 0.4))
    n_weak_chapter = max(1, round(count * 0.3))
    n_difficulty = max(1, round(count * 0.2))
    n_random = count - n_unmastered - n_weak_chapter - n_difficulty
    if n_random < 0:
        n_random = 0

    unmastered_records = db.query(MasteryRecord).filter(
        MasteryRecord.user_id == user_id,
        MasteryRecord.status == "unmastered",
    ).all()
    unmastered_qids = {mr.question_id for mr in unmastered_records}
    unmastered_pool = [q for q in all_questions if q.id in unmastered_qids]
    random.shuffle(unmastered_pool)

    by_chapter = (
        db.query(
            Question.chapter,
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id, Question.chapter != "")
        .group_by(Question.chapter)
        .all()
    )
    weak_chapters = set()
    for ch, t, c in by_chapter:
        acc = (c or 0) / t if t > 0 else 0
        if acc < 0.6:
            weak_chapters.add(ch)
    weak_chapter_pool = [q for q in all_questions if q.chapter in weak_chapters]
    random.shuffle(weak_chapter_pool)

    total_records = db.query(Record).filter(Record.user_id == user_id).count()
    correct_records = db.query(Record).filter(Record.user_id == user_id, Record.is_correct == True).count()
    user_accuracy = correct_records / total_records if total_records > 0 else 0.5

    if user_accuracy > 0.8:
        target_difficulty = [3, 4, 5]
    elif user_accuracy < 0.4:
        target_difficulty = [1, 2]
    else:
        target_difficulty = [2, 3]
    difficulty_pool = [q for q in all_questions if q.difficulty in target_difficulty]
    random.shuffle(difficulty_pool)

    random_pool = list(all_questions)
    random.shuffle(random_pool)

    selected = []
    selected_ids = set()

    def _pick(pool, n, reason):
        picked = []
        for q in pool:
            if q.id not in selected_ids and len(picked) < n:
                selected_ids.add(q.id)
                picked.append((q, reason))
        return picked

    selected.extend(_pick(unmastered_pool, n_unmastered, "错题复习"))
    selected.extend(_pick(weak_chapter_pool, n_weak_chapter, "薄弱章节"))
    selected.extend(_pick(difficulty_pool, n_difficulty, "难度适配"))
    selected.extend(_pick(random_pool, n_random, "随机补充"))

    if len(selected) < count:
        remaining = [q for q in all_questions if q.id not in selected_ids]
        random.shuffle(remaining)
        for q in remaining:
            if len(selected) >= count:
                break
            selected_ids.add(q.id)
            selected.append((q, "随机补充"))

    return selected[:count]


@router.get("/practice")
def practice_page(
    request: Request,
    subject: str = "",
    semester: str = "",
    chapter: str = "",
    count: int = 10,
    mode: str = "smart",
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = require_non_guest(request, db)
    if mode in ("smart", "adaptive"):
        smart_result = _smart_select(user_id, db, subject, semester, chapter, count, mode=mode)
        selected = [q for q, _ in smart_result]
    else:
        query = db.query(Question)
        if subject:
            query = query.filter(Question.subject == subject)
        if semester:
            query = query.filter(Question.semester == semester)
        if chapter:
            query = query.filter(Question.chapter == chapter)
        all_questions = query.all()
        if not all_questions:
            return request.app.state.templates.TemplateResponse(
                "student/no_questions.html",
                {"request": request, "subject": subject, "subjects": SUBJECTS},
            )
        answered_ids = [
            r[0] for r in db.query(Record.question_id)
            .filter(Record.user_id == user_id).distinct().all()
        ]
        unanswered = [q for q in all_questions if q.id not in answered_ids]
        pool = unanswered if unanswered else all_questions
        selected = random.sample(pool, min(count, len(pool)))

    if not selected:
        return request.app.state.templates.TemplateResponse(
            "student/no_questions.html",
            {"request": request, "subject": subject, "subjects": SUBJECTS},
        )

    return request.app.state.templates.TemplateResponse(
        "student/practice.html",
        {
            "request": request,
            "questions": selected,
            "subject": subject,
            "subjects": SUBJECTS,
            "question_types": QUESTION_TYPES,
            "mode": mode,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.post("/practice/submit")
async def submit_practice(
    request: Request,
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    results = []
    correct_count = 0
    total = 0

    question_ids = []
    for key in form:
        if key.startswith("answer_"):
            qid_str = key.replace("answer_", "")
            try:
                qid = int(qid_str)
            except ValueError:
                continue
            if qid not in question_ids:
                question_ids.append(qid)

    questions = {q.id: q for q in db.query(Question).filter(Question.id.in_(question_ids)).all()}

    for qid in question_ids:
        question = questions.get(qid)
        if not question:
            continue
        if question.q_type == "multi_choice":
            vals = form.getlist(f"answer_{qid}")
            user_answer = "".join(sorted([v.upper() for v in vals]))
        else:
            user_answer = form.get(f"answer_{qid}", "")
        is_correct = check_answer(question, user_answer)
        if is_correct:
            correct_count += 1
        total += 1
        record = Record(
            user_id=user_id,
            question_id=qid,
            user_answer=user_answer,
            is_correct=is_correct,
        )
        db.add(record)

        mastery = db.query(MasteryRecord).filter(
            MasteryRecord.user_id == user_id,
            MasteryRecord.question_id == qid,
        ).first()
        if mastery is None:
            mastery = MasteryRecord(
                user_id=user_id,
                question_id=qid,
                status="unmastered",
                consecutive_correct=0,
            )
            db.add(mastery)
            db.flush()

        if is_correct:
            mastery.consecutive_correct += 1
            if mastery.consecutive_correct >= 3:
                mastery.status = "mastered"
            else:
                mastery.status = "reviewing"
        else:
            mastery.consecutive_correct = 0
            mastery.status = "unmastered"

        results.append(
            {
                "question": question,
                "user_answer": user_answer,
                "is_correct": is_correct,
            }
        )
    db.commit()
    accuracy = round(correct_count / total * 100, 1) if total > 0 else 0

    return request.app.state.templates.TemplateResponse(
        "student/result.html",
        {
            "request": request,
            "results": results,
            "correct_count": correct_count,
            "total": total,
            "accuracy": accuracy,
            "question_types": QUESTION_TYPES,
        },
    )


@router.get("/mistakes")
def mistake_book(
    request: Request,
    subject: str = "",
    status: str = "",
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = require_non_guest(request, db)
    wrong_records = (
        db.query(Record)
        .filter(Record.user_id == user_id, Record.is_correct == False)
        .order_by(Record.created_at.desc())
        .all()
    )

    seen = set()
    unique_mistakes = []
    for r in wrong_records:
        if r.question_id not in seen:
            seen.add(r.question_id)
            unique_mistakes.append(r)

    if subject:
        unique_mistakes = [r for r in unique_mistakes if r.question.subject == subject]

    wrong_qids = list(seen)
    mastery_map = {}
    if wrong_qids:
        mastery_records = (
            db.query(MasteryRecord)
            .filter(MasteryRecord.user_id == user_id, MasteryRecord.question_id.in_(wrong_qids))
            .all()
        )
        for mr in mastery_records:
            mastery_map[mr.question_id] = mr

    if status:
        filtered = []
        for r in unique_mistakes:
            mr = mastery_map.get(r.question_id)
            ms = mr.status if mr else "unmastered"
            if ms == status:
                filtered.append(r)
        unique_mistakes = filtered

    all_wrong_unique = []
    seen2 = set()
    for r in db.query(Record).filter(Record.user_id == user_id, Record.is_correct == False).order_by(Record.created_at.desc()).all():
        if r.question_id not in seen2:
            seen2.add(r.question_id)
            all_wrong_unique.append(r)

    if subject:
        all_wrong_unique = [r for r in all_wrong_unique if r.question.subject == subject]

    all_wrong_qids = list(seen2)
    all_mastery_map = {}
    if all_wrong_qids:
        all_mr = db.query(MasteryRecord).filter(
            MasteryRecord.user_id == user_id, MasteryRecord.question_id.in_(all_wrong_qids)
        ).all()
        for mr in all_mr:
            all_mastery_map[mr.question_id] = mr

    status_counts = {"unmastered": 0, "reviewing": 0, "mastered": 0}
    for r in all_wrong_unique:
        mr = all_mastery_map.get(r.question_id)
        ms = mr.status if mr else "unmastered"
        status_counts[ms] = status_counts.get(ms, 0) + 1

    return request.app.state.templates.TemplateResponse(
        "student/mistakes.html",
        {
            "request": request,
            "mistakes": unique_mistakes,
            "mastery_map": mastery_map,
            "subject": subject,
            "subjects": SUBJECTS,
            "question_types": QUESTION_TYPES,
            "status_filter": status,
            "status_counts": status_counts,
        },
    )


@router.get("/mistakes/retry")
def retry_mistakes(
    request: Request,
    subject: str = "",
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = require_non_guest(request, db)
    wrong_records = (
        db.query(Record)
        .filter(Record.user_id == user_id, Record.is_correct == False)
        .all()
    )

    seen = set()
    wrong_qids = []
    for r in wrong_records:
        if r.question_id not in seen:
            seen.add(r.question_id)
            wrong_qids.append(r.question_id)

    still_wrong = []
    if wrong_qids:
        mastery_records = db.query(MasteryRecord).filter(
            MasteryRecord.user_id == user_id,
            MasteryRecord.question_id.in_(wrong_qids),
            MasteryRecord.status != "mastered",
        ).all()
        still_wrong = [mr.question_id for mr in mastery_records]
        no_mastery = [qid for qid in wrong_qids if qid not in {mr.question_id for mr in mastery_records}]
        still_wrong.extend(no_mastery)

    questions = db.query(Question).filter(Question.id.in_(still_wrong)).all()
    if subject:
        questions = [q for q in questions if q.subject == subject]

    if not questions:
        return request.app.state.templates.TemplateResponse(
            "student/mistakes.html",
            {
                "request": request,
                "mistakes": [],
                "mastery_map": {},
                "subject": subject,
                "subjects": SUBJECTS,
                "question_types": QUESTION_TYPES,
                "status_filter": "",
                "status_counts": {"unmastered": 0, "reviewing": 0, "mastered": 0},
                "message": "没有未掌握的错题，继续保持！",
            },
        )

    return request.app.state.templates.TemplateResponse(
        "student/practice.html",
        {
            "request": request,
            "questions": questions,
            "subject": subject,
            "subjects": SUBJECTS,
            "question_types": QUESTION_TYPES,
            "mode": "retry",
        },
    )


@router.get("/analysis")
def weak_analysis(
    request: Request,
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = require_non_guest(request, db)

    by_subject = (
        db.query(
            Question.subject,
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id)
        .group_by(Question.subject)
        .all()
    )
    subject_stats = [
        {
            "name": s,
            "total": t,
            "correct": c or 0,
            "accuracy": round((c or 0) / t * 100, 1) if t > 0 else 0,
        }
        for s, t, c in by_subject
    ]
    subject_stats.sort(key=lambda x: x["accuracy"])

    by_chapter = (
        db.query(
            Question.subject,
            Question.chapter,
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id, Question.chapter != "")
        .group_by(Question.subject, Question.chapter)
        .all()
    )
    chapter_stats = [
        {
            "subject": s,
            "chapter": ch,
            "total": t,
            "correct": c or 0,
            "accuracy": round((c or 0) / t * 100, 1) if t > 0 else 0,
        }
        for s, ch, t, c in by_chapter
    ]
    chapter_stats.sort(key=lambda x: x["accuracy"])

    by_type = (
        db.query(
            Question.q_type,
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id)
        .group_by(Question.q_type)
        .all()
    )
    type_stats = [
        {
            "type": QUESTION_TYPES.get(qt, qt),
            "total": t,
            "correct": c or 0,
            "accuracy": round((c or 0) / t * 100, 1) if t > 0 else 0,
        }
        for qt, t, c in by_type
    ]

    weak_subjects = [s for s in subject_stats if s["accuracy"] < 60]
    weak_chapters = [c for c in chapter_stats if c["accuracy"] < 60]

    return request.app.state.templates.TemplateResponse(
        "student/analysis.html",
        {
            "request": request,
            "subject_stats": subject_stats,
            "chapter_stats": chapter_stats,
            "type_stats": type_stats,
            "weak_subjects": weak_subjects,
            "weak_chapters": weak_chapters,
        },
    )


@router.get("/profile")
def profile(
    request: Request,
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = require_non_guest(request, db)
    total = db.query(Record).filter(Record.user_id == user_id).count()
    correct = db.query(Record).filter(Record.user_id == user_id, Record.is_correct == True).count()
    accuracy = round(correct / total * 100, 1) if total > 0 else 0

    first_record = db.query(Record).filter(Record.user_id == user_id).order_by(Record.created_at).first()
    if first_record:
        first_date = first_record.created_at.date()
        today = datetime.now().date()
        study_days = (today - first_date).days + 1
    else:
        study_days = 0

    active_days = db.query(sa_func.date(Record.created_at)).filter(Record.user_id == user_id).distinct().count()

    today_count = db.query(Record).filter(
        Record.user_id == user_id,
        sa_func.date(Record.created_at) == datetime.now().date()
    ).count()

    streak = 0
    recent_dates = set(
        str(d[0]) for d in db.query(sa_func.date(Record.created_at))
        .filter(Record.user_id == user_id)
        .distinct()
        .limit(365)
        .all()
    )
    check_date = datetime.now().date()
    while True:
        if str(check_date) in recent_dates:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            if streak == 0 and check_date == datetime.now().date():
                check_date -= timedelta(days=1)
                continue
            break

    daily = (
        db.query(
            sa_func.date(Record.created_at).label("date"),
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .filter(Record.user_id == user_id)
        .group_by(sa_func.date(Record.created_at))
        .order_by(sa_func.date(Record.created_at).desc())
        .limit(14)
        .all()
    )
    daily_stats = [
        {"date": str(d), "total": t, "correct": c or 0, "accuracy": round((c or 0) / t * 100, 1) if t > 0 else 0}
        for d, t, c in daily
    ]
    daily_stats.reverse()

    by_subject = (
        db.query(
            Question.subject,
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id)
        .group_by(Question.subject)
        .all()
    )
    subject_stats = [
        {"name": s, "total": t, "correct": c or 0, "accuracy": round((c or 0) / t * 100, 1) if t > 0 else 0}
        for s, t, c in by_subject
    ]
    subject_stats.sort(key=lambda x: x["accuracy"])

    wrong_qids = set(
        r[0] for r in db.query(Record.question_id)
        .filter(Record.user_id == user_id, Record.is_correct == False).distinct().all()
    )
    mastered = set()
    if wrong_qids:
        corrected = (
            db.query(Record.question_id)
            .filter(Record.user_id == user_id, Record.question_id.in_(wrong_qids), Record.is_correct == True)
            .distinct()
            .all()
        )
        mastered = set(r[0] for r in corrected)
    mistake_count = len(wrong_qids - mastered)

    active_plan = db.query(StudyPlan).filter(StudyPlan.user_id == user_id, StudyPlan.active == True).first()
    daily_goal = active_plan.daily_goal if active_plan else 10
    today_goal_pct = min(round(today_count / daily_goal * 100, 1), 100) if daily_goal > 0 else 0

    now = datetime.now()
    recent_7_start = now - timedelta(days=7)
    prev_7_start = now - timedelta(days=14)
    recent_7 = db.query(Record).filter(Record.user_id == user_id, Record.created_at >= recent_7_start).all()
    prev_7 = db.query(Record).filter(Record.user_id == user_id, Record.created_at >= prev_7_start, Record.created_at < recent_7_start).all()
    recent_7_acc = sum(1 for r in recent_7 if r.is_correct) / len(recent_7) * 100 if recent_7 else 0
    prev_7_acc = sum(1 for r in prev_7 if r.is_correct) / len(prev_7) * 100 if prev_7 else 0
    accuracy_change = round(recent_7_acc - prev_7_acc, 1)

    chapter_badges = (
        db.query(
            Question.subject,
            Question.chapter,
            sa_func.count(Record.id),
            sa_func.sum(sa_func.cast(Record.is_correct, Integer)),
        )
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id, Question.chapter != "")
        .group_by(Question.subject, Question.chapter)
        .all()
    )
    badges = [
        {"subject": s, "chapter": ch, "accuracy": round((c or 0) / t * 100, 1)}
        for s, ch, t, c in chapter_badges
        if t > 0 and (c or 0) / t > 0.8
    ]

    return request.app.state.templates.TemplateResponse(
        "student/profile.html",
        {
            "request": request,
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "study_days": study_days,
            "active_days": active_days,
            "today_count": today_count,
            "streak": streak,
            "daily_stats": daily_stats,
            "subject_stats": subject_stats,
            "mistake_count": mistake_count,
            "today_goal_pct": today_goal_pct,
            "daily_goal": daily_goal,
            "accuracy_change": accuracy_change,
            "badges": badges,
        },
    )


@router.get("/records")
def my_records(
    request: Request,
    db: Annotated[Session, Depends(get_db)] = None,
):
    user_id = require_non_guest(request, db)
    total = db.query(Record).filter(Record.user_id == user_id).count()
    correct = (
        db.query(Record)
        .filter(Record.user_id == user_id, Record.is_correct == True)
        .count()
    )
    accuracy = round(correct / total * 100, 1) if total > 0 else 0

    by_subject = (
        db.query(Question.subject, sa_func.count(Record.id), sa_func.sum(sa_func.cast(Record.is_correct, Integer)))
        .join(Question, Record.question_id == Question.id)
        .filter(Record.user_id == user_id)
        .group_by(Question.subject)
        .all()
    )
    subject_stats = [
        {"subject": s, "total": t, "correct": c or 0, "accuracy": round((c or 0) / t * 100, 1) if t > 0 else 0}
        for s, t, c in by_subject
    ]

    recent = (
        db.query(Record)
        .filter(Record.user_id == user_id)
        .order_by(Record.created_at.desc())
        .limit(50)
        .all()
    )

    return request.app.state.templates.TemplateResponse(
        "student/records.html",
        {
            "request": request,
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "subject_stats": subject_stats,
            "recent": recent,
            "question_types": QUESTION_TYPES,
        },
    )


@router.post("/favorites/{question_id}/add")
async def add_favorite(question_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    existing = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.question_id == question_id).first()
    if not existing:
        db.add(Favorite(user_id=user_id, question_id=question_id))
        db.commit()
    hx_request = request.headers.get("hx-request") == "true"
    if hx_request:
        return Response(content='<button hx-post="/student/favorites/' + str(question_id) + '/remove" hx-target="this" hx-swap="outerHTML" class="btn btn-primary btn-sm">已收藏</button>', media_type="text/html")
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)


@router.post("/favorites/{question_id}/remove")
async def remove_favorite(question_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    fav = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.question_id == question_id).first()
    if fav:
        db.delete(fav)
        db.commit()
    hx_request = request.headers.get("hx-request") == "true"
    if hx_request:
        return Response(content='<button hx-post="/student/favorites/' + str(question_id) + '/add" hx-target="this" hx-swap="outerHTML" class="btn btn-outline btn-sm">收藏</button>', media_type="text/html")
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)


@router.get("/favorites")
def favorites_page(request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    favs = db.query(Favorite).filter(Favorite.user_id == user_id).order_by(Favorite.created_at.desc()).all()
    questions = []
    for f in favs:
        q = db.query(Question).filter(Question.id == f.question_id).first()
        if q:
            questions.append(q)
    return request.app.state.templates.TemplateResponse(
        "student/favorites.html",
        {"request": request, "questions": questions, "question_types": QUESTION_TYPES},
    )


@router.get("/plans")
def plans_page(request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    plans = db.query(StudyPlan).filter(StudyPlan.user_id == user_id).order_by(StudyPlan.created_at.desc()).all()
    from datetime import date
    today = date.today()
    today_records = db.query(Record).filter(
        Record.user_id == user_id,
        sa_func.date(Record.created_at) == today,
    ).count()
    return request.app.state.templates.TemplateResponse(
        "student/plans.html",
        {"request": request, "plans": plans, "today_count": today_records, "subjects": SUBJECTS, "semesters": SEMESTERS},
    )


@router.post("/plans/create")
async def create_plan(request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    form = await request.form()
    plan = StudyPlan(
        user_id=user_id,
        subject=form.get("subject", ""),
        semester=form.get("semester", ""),
        daily_goal=int(form.get("daily_goal", "10")),
    )
    db.add(plan)
    db.commit()
    return RedirectResponse(url="/student/plans", status_code=303)


@router.post("/plans/{plan_id}/delete")
async def delete_plan(plan_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id, StudyPlan.user_id == user_id).first()
    if plan:
        db.delete(plan)
        db.commit()
    return RedirectResponse(url="/student/plans", status_code=303)


@router.get("/notifications")
def notifications_page(request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    notifications = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    unread_count = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).count()
    return request.app.state.templates.TemplateResponse(
        "student/notifications.html",
        {"request": request, "notifications": notifications, "unread_count": unread_count},
    )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if n:
        n.is_read = True
        db.commit()
    return RedirectResponse(url="/student/notifications", status_code=303)


@router.post("/notifications/read-all")
async def mark_all_notifications_read(request: Request, db: Session = Depends(get_db)):
    user_id = require_non_guest(request, db)
    await validate_csrf_async(request)
    db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return RedirectResponse(url="/student/notifications", status_code=303)
