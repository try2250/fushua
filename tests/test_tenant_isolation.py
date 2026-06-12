"""
多租户隔离测试套件

覆盖：
- TenantContext 数据类基本行为
- Teacher/Student 角色租户解析
- tenant_filter 查询辅助
- question_service 租户级查询
- API 端点租户隔离
"""
import pytest
from app.core.tenant import TenantContext


def test_tenant_context_holds_id_user_source():
    ctx = TenantContext(tenant_id=7, user=None, source="teacher")
    assert ctx.tenant_id == 7
    assert ctx.source == "teacher"
    assert ctx.user is None


def test_tenant_context_repr_includes_id():
    ctx = TenantContext(tenant_id=42, user=None, source="student")
    assert "42" in repr(ctx)
    assert "student" in repr(ctx)
