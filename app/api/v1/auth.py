from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    WechatLoginRequest, WechatLoginResponse,
    WechatBindRequest, SendSMSRequest,
    LoginRequest, TokenResponse
)
from app.schemas.common import ResponseModel
from app.services.auth_service import auth_service
from app.models import User
from app.core.security import verify_token


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ResponseModel[TokenResponse])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = auth_service.create_token_for_user(user)

    return ResponseModel(data=TokenResponse(
        token=token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "display_name": user.display_name
        }
    ))


@router.post("/wechat/login", response_model=ResponseModel[WechatLoginResponse])
def wechat_login(request: WechatLoginRequest, db: Session = Depends(get_db)):
    result = auth_service.wechat_login(db, request.code)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ResponseModel(data=WechatLoginResponse(**result))


@router.post("/wechat/bind", response_model=ResponseModel[TokenResponse])
def wechat_bind(request: WechatBindRequest, db: Session = Depends(get_db)):
    payload = verify_token(request.openid_token)
    if not payload or not payload.get("temp"):
        raise HTTPException(status_code=401, detail="无效的临时 token")

    openid = payload["openid"]

    if not auth_service.verify_code(db, request.phone, request.code, "bind"):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    existing_user = db.query(User).filter(User.phone == request.phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="手机号已注册")

    user = User(
        username=f"wx_{openid[:8]}",
        password_hash="",
        role=request.role,
        phone=request.phone,
        openid=openid,
        is_phone_verified=True,
        class_id=request.class_id if request.role == "student" else None
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth_service.create_token_for_user(user)

    return ResponseModel(data=TokenResponse(
        token=token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "phone": user.phone
        }
    ))


@router.post("/sms/send", response_model=ResponseModel[dict])
def send_sms(request: SendSMSRequest, db: Session = Depends(get_db)):
    code = auth_service.generate_verification_code(db, request.phone, request.purpose)
    return ResponseModel(data={"message": "验证码已发送"})
