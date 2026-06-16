import os
import secrets
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
import logging
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import engine, Base, SessionLocal, get_db
from app.routers import pages, auth, teacher, student, assignment, classgroup, extractor, backup, classroom, platform, platform_users, platform_recovery, platform_classes, platform_audit, platform_announcements, platform_export, platform_batch_cleanup, platform_notifications, teacher_review, teacher_stats
from app.models import User, Notification
from app.core.config import settings
from app.middleware import RequestTrackingMiddleware
from app.core.request_context import RequestContextMiddleware
from app.utils.logger import log_error, log_warning, log_info
from app.utils.error_monitor import error_monitor

from app.core.observability import init_sentry, init_structlog
init_structlog()
init_sentry()

if not os.environ.get("DATABASE_URL", "").startswith("postgresql"):
    Base.metadata.create_all(bind=engine)

from app.models import SiteConfig, User as InitUser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("fushua")

_init_db = SessionLocal()

# Seed default PlatformAdmin on first run
from app.models import PlatformAdmin as _PA
_default_pa = _init_db.query(_PA).first()
if not _default_pa:
    _init_db.add(_PA(
        username="root",
        password_hash=_PA.hash_password("rootpass"),
        email="root@fushua.local",
    ))
    _init_db.commit()
    logger.info("默认平台管理员已创建 — root / rootpass")
_init_db.close()

_is_production = os.environ.get("ENVIRONMENT", "development") == "production"

app = FastAPI(
    title="付刷 API",
    description="付刷项目 RESTful API 文档",
    version="4.0.0",
    docs_url=None if _is_production else "/api/docs",
    redoc_url=None if _is_production else "/api/redoc",
    openapi_url=None if _is_production else "/api/openapi.json",
)

@app.on_event("startup")
def startup_event():
    try:
        from app.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        import sys
        print(f"[scheduler] start failed (non-fatal): {e}", file=sys.stderr)


SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-key-" + secrets.token_hex(32)
    import warnings
    warnings.warn("使用开发模式密钥，生产环境请设置 SECRET_KEY 环境变量！")

HTTPS_ONLY = os.environ.get("HTTPS_ONLY", "false").lower() == "true"


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestTrackingMiddleware)


class CSRFSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "csrf_token" not in request.session:
            request.session["csrf_token"] = secrets.token_hex(16)
        response = await call_next(request)
        return response


app.add_middleware(CSRFSessionMiddleware)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
        return response


app.add_middleware(SecurityHeadersMiddleware)

@app.get("/health")
def health():
    import time
    from app.core.metrics import request_counter, error_counter
    db = SessionLocal()
    t0 = time.perf_counter()
    try:
        db.execute(__import__('sqlalchemy').text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        db.close()
    db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "status": "ok" if db_ok else "degraded",
        "db_ok": db_ok,
        "db_latency_ms": db_latency_ms,
        "request_count_5m": request_counter.count(),
        "error_count_5m": error_counter.count(),
    }

app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=HTTPS_ONLY,
    max_age=86400 * 7,  # 7天会话有效期
)


class CookieHardeningMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        async def send_with_httponly(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                new_headers = []
                for name, value in headers:
                    if name == b"set-cookie":
                        cookie_str = value.decode("latin-1")
                        if cookie_str.startswith("session=") and "httponly" not in cookie_str.lower():
                            cookie_str += "; HttpOnly"
                            value = cookie_str.encode("latin-1")
                    new_headers.append((name, value))
                message["headers"] = new_headers
            await send(message)

        await self.app(scope, receive, send_with_httponly)


app.add_middleware(CookieHardeningMiddleware)

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _get_session_factory():
    if get_db in app.dependency_overrides:
        gen = app.dependency_overrides[get_db]()
        db = next(gen)
        return db, lambda: gen.close()
    db = SessionLocal()
    return db, db.close


def _global_template_vars(request: Request) -> dict:
    user_id = request.session.get("user_id")
    logged_in = user_id is not None
    role = ""
    display_name = ""
    is_guest = False
    is_admin = False
    unread_count = 0
    if logged_in:
        db, cleanup = _get_session_factory()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                role = user.role
                display_name = user.display_name
                is_guest = user.is_guest
                if role == "student":
                    unread_count = db.query(Notification).filter(
                        Notification.user_id == user.id, Notification.is_read == False
                    ).count()
        finally:
            cleanup()
    return {
        "logged_in": logged_in,
        "role": role,
        "display_name": display_name,
        "is_guest": is_guest,
        "is_admin": is_admin,
        "unread_count": unread_count,
        "csrf_token": request.session.get("csrf_token", ""),
    }


original_template_response = templates.TemplateResponse


def custom_template_response(name, context, **kwargs):
    request = context.get("request")
    if request:
        global_vars = _global_template_vars(request)
        for k, v in global_vars.items():
            if k not in context:
                context[k] = v
    return original_template_response(name, context, **kwargs)


templates.TemplateResponse = custom_template_response

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 303:
        location = exc.headers.get("Location", "/") if exc.headers else "/"
        return RedirectResponse(url=location, status_code=303)

    # 记录 4xx 和 5xx 错误
    if exc.status_code >= 400:
        request_id = getattr(request.state, "request_id", "unknown")
        user_id = getattr(request.state, "user_id", None)

        if exc.status_code >= 500:
            log_error(f"HTTP {exc.status_code}: {exc.detail}", request)
            error_monitor.add_error(
                request_id=request_id,
                user_id=user_id,
                path=request.url.path,
                method=request.method,
                error_type="HTTPException",
                error_message=str(exc.detail),
                status_code=exc.status_code
            )
        elif exc.status_code in [403, 404]:
            log_warning(f"HTTP {exc.status_code}: {exc.detail}", request)

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code * 100, "message": exc.detail, "data": None},
        )
    error_map = {
        400: ("请求错误", "您的请求无法被处理，请检查输入后重试"),
        403: ("访问被拒绝", "您没有权限执行此操作"),
        404: ("页面未找到", "您访问的页面不存在或已被删除"),
        405: ("方法不允许", "该请求方法不被允许"),
        429: ("请求过于频繁", "操作过于频繁，请稍后再试"),
        500: ("服务器错误", "服务器内部发生错误，请稍后重试"),
    }
    title, message = error_map.get(exc.status_code, ("出错了", "发生了未知错误"))
    safe_details = {
        "作业不存在", "您不属于该作业班级", "该作业未绑定班级，无法完成",
        "题目不存在", "题库不存在", "班级不存在",
        "Invalid class id", "请选择班级",
    }
    if exc.detail and exc.detail in safe_details:
        message = exc.detail
    return request.app.state.templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": exc.status_code, "error_title": title, "error_message": message},
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    user_id = getattr(request.state, "user_id", None)

    log_warning(f"参数验证失败: {exc.errors()}", request)

    if request.url.path.startswith("/api/"):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"]
            })
        return JSONResponse(
            status_code=422,
            content={"code": 10001, "message": "参数验证失败", "data": {"errors": errors}},
        )
    return request.app.state.templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": 400, "error_title": "请求错误", "error_message": "提交的数据格式不正确"},
        status_code=400,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    user_id = getattr(request.state, "user_id", None)

    log_error(f"未处理的异常: {type(exc).__name__}: {str(exc)}", request, exc_info=True)

    error_monitor.add_error(
        request_id=request_id,
        user_id=user_id,
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
        status_code=500
    )

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"code": 10000, "message": "系统错误", "data": None},
        )
    return request.app.state.templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": 500, "error_title": "服务器错误", "error_message": "服务器内部发生错误，请稍后重试"},
        status_code=500,
    )

app.state.templates = templates

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(assignment.router)
app.include_router(classgroup.router)
app.include_router(platform.router)
app.include_router(platform_users.router)
app.include_router(platform_recovery.router)
app.include_router(platform_classes.router)
app.include_router(platform_audit.router)
app.include_router(platform_announcements.router)
app.include_router(platform_export.router)
app.include_router(platform_batch_cleanup.router)
app.include_router(platform_notifications.router)
app.include_router(extractor.router)
app.include_router(backup.router)
app.include_router(classroom.router)
app.include_router(teacher_review.router)
app.include_router(teacher_stats.router)

from app.api.v1 import auth as api_auth, users as api_users, classes as api_classes, questions as api_questions, assignments as api_assignments, records as api_records, announcements as api_announcements, classroom as api_classroom, client_error, practice as api_practice, badges, onboarding, notifications as api_notifications, comments as api_comments
app.include_router(api_auth.router, prefix="/api/v1")
app.include_router(api_users.router, prefix="/api/v1")
app.include_router(api_classes.router, prefix="/api/v1")
app.include_router(api_questions.router, prefix="/api/v1")
app.include_router(api_assignments.router, prefix="/api/v1")
app.include_router(api_records.router, prefix="/api/v1")
app.include_router(api_records.practice_router, prefix="/api/v1")
app.include_router(api_announcements.router, prefix="/api/v1")
app.include_router(api_classroom.router, prefix="/api/v1")
app.include_router(client_error.router, prefix="/api/v1")
app.include_router(api_practice.router, prefix="/api/v1")
app.include_router(badges.router, prefix="/api/v1")
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(api_notifications.router, prefix="/api/v1")
app.include_router(api_comments.router, prefix="/api/v1")
