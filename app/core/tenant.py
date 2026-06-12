"""
多租户基础设施

核心概念：
- TenantContext：封装当前请求的租户上下文（tenant_id = 老师 user.id）
- get_tenant_context：FastAPI 依赖，从请求中解析租户身份
- tenant_filter：SQLAlchemy 查询辅助，按 created_by 过滤
"""
from dataclasses import dataclass
from typing import Optional, Literal

from app.models import User

TenantSource = Literal["teacher", "student", "platform_admin"]


@dataclass
class TenantContext:
    tenant_id: int
    user: Optional[User]
    source: TenantSource

    def __repr__(self) -> str:
        user_id = self.user.id if self.user is not None else None
        return f"TenantContext(tenant_id={self.tenant_id}, source={self.source}, user_id={user_id})"
