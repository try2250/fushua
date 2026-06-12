"""路由审计扫描器 — 自动检测缺失 tenant 依赖的 API 路由"""
import inspect
import pytest
from fastapi.routing import APIRoute
from app.main import app
from app.core.tenant import get_tenant_context


# 白名单：登录/注册/微信认证/短信/健康检查/文档等不需要 tenant 的路径
WHITELIST_PATH_PREFIXES = [
    "/api/v1/auth/",
    "/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/docs/oauth2-redirect",
]


def _depends_on_tenant(route: APIRoute) -> bool:
    """检查路由是否声明了 get_tenant_context 依赖"""
    if not hasattr(route, "endpoint"):
        return False
    sig = inspect.signature(route.endpoint)
    for param in sig.parameters.values():
        default = param.default
        if hasattr(default, "dependency") and default.dependency is get_tenant_context:
            return True
    return False


def test_all_api_v1_routes_declare_tenant_dep():
    missing = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/api/v1/"):
            continue
        if any(route.path.startswith(p) for p in WHITELIST_PATH_PREFIXES):
            continue
        if not _depends_on_tenant(route):
            missing.append(f"{list(route.methods)} {route.path}")
    if missing:
        # Plan 1.1 只覆盖 questions；其他路由在 1.2 完成前 xfail
        question_missing = [m for m in missing if "/api/v1/questions" in m]
        assert not question_missing, f"Question routes missing tenant dep: {question_missing}"
        pytest.xfail(f"Other routes pending (Plan 1.2): {missing}")
