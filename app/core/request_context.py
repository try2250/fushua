"""请求级上下文：request_id / user_id / tenant_id 注入到 structlog。"""
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog
from app.core.metrics import request_counter, error_counter


def _new_request_id() -> str:
    return secrets.token_hex(8)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or _new_request_id()
        user_id = None
        try:
            session = getattr(request, "session", None)
            if session:
                user_id = session.get("user_id")
        except Exception:
            pass

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=rid, user_id=user_id)
        request_counter.record()
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                error_counter.record()
        except Exception:
            error_counter.record()
            raise
        finally:
            response_obj = locals().get("response")
            if response_obj is not None:
                response_obj.headers["x-request-id"] = rid
            structlog.contextvars.clear_contextvars()
        return response
