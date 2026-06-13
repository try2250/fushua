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

# 精确路径白名单：跨租户入口（学生主动加入）
WHITELIST_EXACT_PATHS = [
    "/api/v1/classes/{class_id}/join",
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
        if route.path in WHITELIST_EXACT_PATHS:
            continue
        if not _depends_on_tenant(route):
            missing.append(f"{list(route.methods)} {route.path}")
    if missing:
        # Plan 1.2A 覆盖 questions/classes/assignments
        COVERED_PREFIXES = [
            "/api/v1/questions",
            "/api/v1/classes",
            "/api/v1/assignments",
        ]
        covered_missing = [
            m for m in missing
            if any(p in m for p in COVERED_PREFIXES)
        ]
        assert not covered_missing, (
            f"Covered resources missing tenant dep: {covered_missing}"
        )
        # 余下 users/records/announcements 等待后续 plan
        pytest.xfail(f"Other routes pending: {missing}")
