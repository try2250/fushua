import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.utils.logger import log_info, log_error


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """为每个请求生成唯一的 request_id，并从 session 中提取 user_id"""

    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        session = getattr(request, 'session', {})
        request.state.user_id = session.get("user_id")
        request.state.user_role = session.get("role")

        # 记录请求开始时间
        start_time = time.time()

        try:
            response = await call_next(request)

            # 计算请求耗时
            duration_ms = (time.time() - start_time) * 1000

            # 记录请求日志
            log_info(
                f"{request.method} {request.url.path}",
                request=request,
                status_code=response.status_code,
                duration_ms=f"{duration_ms:.2f}"
            )

            response.headers["X-Request-ID"] = request.state.request_id

            return response

        except Exception as e:
            # 计算请求耗时
            duration_ms = (time.time() - start_time) * 1000

            # 记录异常日志
            log_error(
                f"{request.method} {request.url.path} - Exception: {str(e)}",
                request=request,
                duration_ms=f"{duration_ms:.2f}",
                exc_info=True
            )
            raise
