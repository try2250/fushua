from sqlalchemy.orm import Session
from app.models import ClassGroup, ClassMember, User
from app.schemas.class_group import ClassGroupCreate, ClassGroupUpdate
from typing import List, Optional


class ClassService:
    def get_classes(self, db: Session, user_id: int, role: str) -> List[ClassGroup]:
        """获取用户的班级列表"""
        if role == "teacher":
            return db.query(ClassGroup).filter(ClassGroup.created_by == user_id).all()
        else:
            member_records = db.query(ClassMember).filter(ClassMember.user_id == user_id).all()
            class_ids = [m.class_id for m in member_records]
            return db.query(ClassGroup).filter(ClassGroup.id.in_(class_ids)).all()

    def create_class(self, db: Session, class_data: ClassGroupCreate, user_id: int) -> ClassGroup:
        """创建班级"""
        new_class = ClassGroup(name=class_data.name, created_by=user_id)
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        return new_class

    def get_class_by_id(self, db: Session, class_id: int) -> Optional[ClassGroup]:
        """获取班级详情"""
        return db.query(ClassGroup).filter(ClassGroup.id == class_id).first()

    def update_class(self, db: Session, class_id: int, class_data: ClassGroupUpdate) -> Optional[ClassGroup]:
        """更新班级"""
        class_obj = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
        if not class_obj:
            return None
        if class_data.name:
            class_obj.name = class_data.name
        db.commit()
        db.refresh(class_obj)
        return class_obj

    def delete_class(self, db: Session, class_id: int) -> bool:
        """删除班级"""
        class_obj = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
        if not class_obj:
            return False
        db.delete(class_obj)
        db.commit()
        return True

    def get_class_members(self, db: Session, class_id: int) -> List[dict]:
        """获取班级成员"""
        members = db.query(ClassMember, User).join(User, ClassMember.user_id == User.id).filter(
            ClassMember.class_id == class_id
        ).all()
        return [
            {
                "id": member.id,
                "user_id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
                "joined_at": member.joined_at
            }
            for member, user in members
        ]

    def join_class(self, db: Session, class_id: int, user_id: int) -> bool:
        """加入班级"""
        existing = db.query(ClassMember).filter(
            ClassMember.class_id == class_id,
            ClassMember.user_id == user_id
        ).first()
        if existing:
            return False
        new_member = ClassMember(class_id=class_id, user_id=user_id)
        db.add(new_member)
        db.commit()
        return True

    def get_classes_for_tenant(self, db: Session, tenant_id: int) -> List[ClassGroup]:
        from app.models import ClassGroup
        return db.query(ClassGroup).filter(
            ClassGroup.created_by == tenant_id
        ).order_by(ClassGroup.created_at.desc()).all()

    def get_class_by_id_for_tenant(self, db: Session, tenant_id: int, class_id: int) -> Optional[ClassGroup]:
        from app.models import ClassGroup
        return db.query(ClassGroup).filter(
            ClassGroup.id == class_id,
            ClassGroup.created_by == tenant_id,
        ).first()


class_service = ClassService()
