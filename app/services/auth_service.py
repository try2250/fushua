from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models import User, VerificationCode
from app.core.security import create_access_token, verify_password, hash_password
from app.services.wechat_service import wechat_service
import random


class AuthService:

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = db.query(User).filter(User.phone == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def create_token_for_user(self, user: User) -> str:
        payload = {
            "user_id": user.id,
            "role": user.role,
            "username": user.username
        }
        if user.openid:
            payload["openid"] = user.openid
        return create_access_token(payload)

    def wechat_login(self, db: Session, code: str) -> dict:
        wechat_data = wechat_service.get_openid(code)
        if not wechat_data:
            return {"error": "获取微信信息失败"}

        openid = wechat_data["openid"]
        user = db.query(User).filter(User.openid == openid).first()

        if user:
            token = self.create_token_for_user(user)
            return {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "avatar_url": user.avatar_url,
                    "role": user.role,
                    "phone": user.phone[:3] + "****" + user.phone[-4:] if user.phone else None
                }
            }
        else:
            temp_token = create_access_token(
                {"openid": openid, "temp": True},
                expires_delta=timedelta(minutes=10)
            )
            return {
                "need_bind": True,
                "openid_token": temp_token
            }

    def generate_verification_code(self, db: Session, phone: str, purpose: str) -> str:
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        verification = VerificationCode(
            phone=phone,
            code=code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        db.add(verification)
        db.commit()
        return code

    def verify_code(self, db: Session, phone: str, code: str, purpose: str) -> bool:
        verification = db.query(VerificationCode).filter(
            VerificationCode.phone == phone,
            VerificationCode.code == code,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not verification:
            return False

        verification.is_used = True
        db.commit()
        return True


auth_service = AuthService()
