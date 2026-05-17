import os
import secrets
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
import logging
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import engine, Base, SessionLocal, get_db
from app.routers import pages, auth, teacher, student, assignment, classgroup, admin, extractor, backup
from app.models import User, Notification

if not os.environ.get("DATABASE_URL", "").startswith("postgresql"):
    Base.metadata.create_all(bind=engine)

from app.models import SiteConfig, User as InitUser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fushua")

_init_db = SessionLocal()
if not _init_db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first():
    _init_db.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    _init_db.commit()
if not _init_db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first():
    _init_db.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    _init_db.commit()
first_admin = _init_db.query(InitUser).filter(InitUser.role == "admin").first()
if not first_admin:
    first_teacher = _init_db.query(InitUser).filter(InitUser.role == "teacher", InitUser.is_admin == True).first()
    if first_teacher:
        first_teacher.role = "admin"
        _init_db.commit()
default_admin_user = _init_db.query(InitUser).filter(InitUser.username == "admin").first()
if not default_admin_user:
    admin_password = secrets.token_hex(8)
    default_admin_user = InitUser(
        username="admin",
        password_hash=InitUser.hash_password(admin_password),
        role="admin",
        display_name="系统管理员",
        is_admin=True,
        force_password_change=True,
    )
    _init_db.add(default_admin_user)
    _init_db.commit()
    logger.info(f"默认管理员已创建 — 用户名: admin, 密码: {admin_password}（请立即登录修改）")
_init_db.close()

_is_production = os.environ.get("ENVIRONMENT", "development") == "production"

app = FastAPI(
    title="付刷",
    version="3.0.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-key-" + secrets.token_hex(32)
    import warnings
    warnings.warn("使用开发模式密钥，生产环境请设置 SECRET_KEY 环境变量！")

HTTPS_ONLY = os.environ.get("HTTPS_ONLY", "false").lower() == "true"


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
def health_check(request: Request):
    from app.models import Question, ClassGroup, Assignment
    checks = {}
    overall = "ok"
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        user_count = db.query(User).count()
        question_count = db.query(Question).count()
        class_count = db.query(ClassGroup).count()
        assignment_count = db.query(Assignment).count()
        db.close()
        checks["database"] = "ok"
        checks["user_count"] = user_count
        checks["question_count"] = question_count
        checks["class_count"] = class_count
        checks["assignment_count"] = assignment_count
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        overall = "degraded"

    import os
    checks["version"] = "3.0.0"
    checks["environment"] = os.environ.get("ENVIRONMENT", "development")

    return {"status": overall, "checks": checks}

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
                is_admin = user.role == "admin"
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
    return request.app.state.templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": 400, "error_title": "请求错误", "error_message": "提交的数据格式不正确"},
        status_code=400,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
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
app.include_router(admin.router)
app.include_router(extractor.router)
app.include_router(backup.router)
