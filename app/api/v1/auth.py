from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    WechatLoginRequest, WechatLoginResponse,
    WechatBindRequest, SendSMSRequest,
    LoginRequest, TokenResponse,
    SendEmailCodeRequest, TeacherRegisterRequest,
)
from app.schemas.common import ResponseModel
from app.services.auth_service import auth_service
from app.models import User
from app.core.security import verify_token
from app.core.config import settings


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

    # 根据配置决定是否需要验证码
    if settings.PHONE_BINDING_REQUIRE_SMS:
        if not auth_service.verify_code(db, request.phone, request.code, "bind"):
            raise HTTPException(status_code=400, detail="验证码错误或已过期")

    if request.role not in ("student", "teacher"):
        raise HTTPException(status_code=400, detail="无效的身份")

    # 检查手机号是否已注册
    existing_user = db.query(User).filter(User.phone == request.phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="手机号已注册")

    # 根据是否验证了短信码设置 is_phone_verified
    is_phone_verified = settings.PHONE_BINDING_REQUIRE_SMS

    user = User(
        username=f"wx_{openid[:8]}",
        password_hash="",
        role=request.role,
        phone=request.phone,
        openid=openid,
        is_phone_verified=is_phone_verified,
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

    # 如果不需要短信验证，返回提示信息
    if not settings.PHONE_BINDING_REQUIRE_SMS:
        return ResponseModel(data={"message": "开发期验证码已跳过，可直接绑定"})

    # TODO: 实际发送短信的逻辑
    return ResponseModel(data={"message": "验证码已发送"})


@router.post("/email/send-code", response_model=ResponseModel[dict])
def send_email_code(request: SendEmailCodeRequest, db: Session = Depends(get_db)):
    from app.services.email_service import email_service as _email_svc, EmailServiceError
    try:
        _email_svc.generate_code(db, request.email, request.purpose)
    except EmailServiceError as e:
        raise HTTPException(status_code=429, detail=str(e))
    return ResponseModel(data={"message": "验证码已发送"})


@router.post("/register-teacher", response_model=ResponseModel[TokenResponse])
def register_teacher(request: TeacherRegisterRequest, db: Session = Depends(get_db)):
    from app.services.email_service import email_service as _email_svc
    if not _email_svc.verify_code(db, request.email, request.code, "register"):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    if db.query(User).filter(User.username == request.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    new_user = User(
        username=request.email,
        password_hash=User.hash_password(request.password),
        role="teacher",
        display_name=request.display_name,
    )
    db.add(new_user); db.commit(); db.refresh(new_user)
    token = auth_service.create_token_for_user(new_user)
    return ResponseModel(data=TokenResponse(
        token=token,
        user={
            "id": new_user.id,
            "username": new_user.username,
            "role": new_user.role,
            "display_name": new_user.display_name,
        }
    ))
