from pydantic import BaseModel, Field
from typing import Optional


class WechatLoginRequest(BaseModel):
    code: str = Field(..., description="微信登录 code")


class WechatLoginResponse(BaseModel):
    token: Optional[str] = None
    need_bind: bool = False
    openid_token: Optional[str] = None
    user: Optional[dict] = None


class WechatBindRequest(BaseModel):
    openid_token: str = Field(..., description="临时 openid token")
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")
    role: str = Field(..., description="角色: student/teacher")
    class_id: Optional[int] = Field(None, description="班级 ID（学生必填）")
    invite_code: Optional[str] = Field(None, description="邀请码（教师必填）")


class SendSMSRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    purpose: str = Field(..., description="用途: register/bind/reset/login")


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名或手机号")
    password: str = Field(..., min_length=6, description="密码")


class TokenResponse(BaseModel):
    token: str
    user: dict
