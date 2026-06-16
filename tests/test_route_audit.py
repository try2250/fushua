"""路由审计扫描器 — 自动检测缺失 tenant 依赖的 API 路由"""
import inspect
import pytest
from fastapi.routing import APIRoute
from app.main import app
from app.core.tenant import get_tenant_context


WHITELIST_PATH_PREFIXES = [
    "/api/v1/auth/",
    "/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/docs/oauth2-redirect",
]

USER_OWNED_PATH_PREFIXES = [
    "/api/v1/users/me",
    "/api/v1/records",
    "/api/v1/practice-records",
    "/api/v1/practice",
    "/api/v1/announcements",
    "/api/v1/client-error",
    "/api/v1/classroom",
]

WHITELIST_EXACT_PATHS = [
    "/api/v1/classes/{class_id}/join",
]


def _depends_on_tenant(route: APIRoute) -> bool:
    if not hasattr(route, "endpoint"):
        return False
    sig = inspect.signature(route.endpoint)
    for param in sig.parameters.values():
        default = param.default
        if hasattr(default, "dependency") and default.dependency is get_tenant_context:
            return True
    return False


def test_all_api_v1_routes_declare_tenant_dep():
    COVERED_PREFIXES = [
        "/api/v1/questions",
        "/api/v1/classes",
        "/api/v1/assignments",
        "/api/v1/users/{user_id}",
    ]
    missing = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/api/v1/"):
            continue
        if any(route.path.startswith(p) for p in WHITELIST_PATH_PREFIXES):
            continue
        if any(route.path.startswith(p) for p in USER_OWNED_PATH_PREFIXES):
            continue
        if route.path in WHITELIST_EXACT_PATHS:
            continue
        if not _depends_on_tenant(route):
            missing.append(f"{list(route.methods)} {route.path}")
    # 不再 xfail：必须为空
    assert missing == [], f"路由未声明 tenant 依赖: {missing}"
