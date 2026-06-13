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
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(default="", description="验证码（开发期可为空）")
    role: str = Field(..., description="角色: student/teacher")
    class_id: Optional[int] = Field(None, description="班级 ID（学生必填）")
    invite_code: Optional[str] = Field(None, description="邀请码（教师必填）")


class SendSMSRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$", description="手机号")
    purpose: str = Field(..., description="用途: register/bind/reset/login")


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名或手机号")
    password: str = Field(..., min_length=6, description="密码")


class TokenResponse(BaseModel):
    token: str
    user: dict


class TeacherRegisterRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    display_name: str = Field(..., description="显示名称")
    code: str = Field(..., description="验证码")


class SendEmailCodeRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    purpose: str = Field("register", description="用途")
