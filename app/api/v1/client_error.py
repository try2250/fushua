"""小程序前端 JS 错误自报端点。"""
from typing import Optional
import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from app.schemas.common import ResponseModel


router = APIRouter(prefix="", tags=["客户端错误上报"])

MAX_STACK_LEN = 16_000
logger = structlog.get_logger("fushua.client_error")


class ClientErrorPayload(BaseModel):
    message: str = Field(..., max_length=2_000)
    stack: Optional[str] = Field(None, max_length=MAX_STACK_LEN)
    page: Optional[str] = Field(None, max_length=200)
    platform: Optional[str] = Field(None, max_length=50)
    ts: Optional[int] = None
    user_agent: Optional[str] = Field(None, max_length=500)
    extra: Optional[dict] = None


@router.post("/client-error", response_model=ResponseModel[dict])
def report_client_error(request: Request, payload: ClientErrorPayload):
    raw_len = int(request.headers.get("content-length", "0"))
    if raw_len > 50_000:
        raise HTTPException(status_code=413, detail="payload 过大")

    logger.warning(
        "client_error",
        message=payload.message,
        page=payload.page,
        platform=payload.platform,
        ts=payload.ts,
        user_agent=payload.user_agent,
        stack=(payload.stack[:1000] if payload.stack else None),
    )

    try:
        import sentry_sdk
        if sentry_sdk.Hub.current.client is not None:
            sentry_sdk.capture_message(
                f"[client] {payload.message}",
                level="warning",
                extras={
                    "page": payload.page, "platform": payload.platform,
                    "stack": (payload.stack[:2000] if payload.stack else None),
                },
            )
    except Exception:
        pass

    return ResponseModel(data={"received": True})
