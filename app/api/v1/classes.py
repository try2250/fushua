from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.schemas.class_group import (
    ClassGroupCreate, ClassGroupUpdate,
    ClassGroupResponse, ClassGroupDetailResponse
)
from app.schemas.common import ResponseModel
from app.services.class_service import class_service
from app.models import User, ClassMember
from typing import List


router = APIRouter(prefix="/classes", tags=["班级管理"])


@router.get("", response_model=ResponseModel[List[ClassGroupResponse]])
def get_classes(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    classes = class_service.get_classes_for_tenant(db, tenant.tenant_id)
    return ResponseModel(data=[
        ClassGroupResponse(
            id=c.id,
            name=c.name,
            created_by=c.created_by,
            created_at=c.created_at,
            member_count=len(class_service.get_class_members(db, c.id))
        )
        for c in classes
    ])


@router.post("", response_model=ResponseModel[ClassGroupResponse])
def create_class(
    class_data: ClassGroupCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    if tenant.source != "teacher":
        raise HTTPException(status_code=403, detail="只有教师可以创建班级")
    new_class = class_service.create_class(db, class_data, tenant.tenant_id)
    return ResponseModel(data=ClassGroupResponse(
        id=new_class.id,
        name=new_class.name,
        created_by=new_class.created_by,
        created_at=new_class.created_at,
        member_count=0
    ))


@router.get("/{class_id}", response_model=ResponseModel[ClassGroupDetailResponse])
def get_class_detail(
    class_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    class_obj = class_service.get_class_by_id_for_tenant(db, tenant.tenant_id, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")
    members = class_service.get_class_members(db, class_id)
    return ResponseModel(data=ClassGroupDetailResponse(
        id=class_obj.id,
        name=class_obj.name,
        created_by=class_obj.created_by,
        created_at=class_obj.created_at,
        member_count=len(members),
        members=members
    ))


@router.put("/{class_id}", response_model=ResponseModel[ClassGroupResponse])
def update_class(
    class_id: int,
    class_data: ClassGroupUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    class_obj = class_service.get_class_by_id_for_tenant(db, tenant.tenant_id, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")
    updated_class = class_service.update_class(db, class_id, class_data)
    return ResponseModel(data=ClassGroupResponse(
        id=updated_class.id,
        name=updated_class.name,
        created_by=updated_class.created_by,
        created_at=updated_class.created_at,
        member_count=len(class_service.get_class_members(db, class_id))
    ))


@router.delete("/{class_id}", response_model=ResponseModel[dict])
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    class_obj = class_service.get_class_by_id_for_tenant(db, tenant.tenant_id, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")
    class_service.delete_class(db, class_id)
    return ResponseModel(data={"message": "班级已删除"})


@router.post("/{class_id}/join", response_model=ResponseModel[dict])
def join_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    class_obj = class_service.get_class_by_id(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")
    success = class_service.join_class(db, class_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="已经加入该班级")
    return ResponseModel(data={"message": "加入班级成功"})


@router.delete("/{class_id}/members/{member_id}", response_model=ResponseModel[dict])
def remove_class_member_for_miniprogram(
    class_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    class_obj = class_service.get_class_by_id_for_tenant(db, tenant.tenant_id, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")
    member = db.query(ClassMember).filter(
        ClassMember.id == member_id,
        ClassMember.class_id == class_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="班级成员不存在")
    db.delete(member)
    db.commit()
    return ResponseModel(data={"message": "成员已移出班级"})
