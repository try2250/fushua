from fastapi.testclient import TestClient
from app.models import User, ClassGroup, ClassMember
from tests.conftest import TestingSessionLocal, create_test_user, create_test_question, get_csrf_token, register_and_login
from app.models import Assignment
from app.routers.permissions import is_admin, teacher_owns_student, teacher_owns_class, teacher_owns_question, teacher_owns_bank


def test_is_admin():
    """测试管理员检查功能"""
    db = TestingSessionLocal()
    try:
        # 创建普通教师
        teacher = create_test_user(db, "teacher_admin_test", "teacher")
        db.commit()
        db.refresh(teacher)
        assert is_admin(db, teacher.id) == False
        
        # 创建管理员
        admin = create_test_user(db, "admin_admin_test", "teacher")
        admin.is_admin = True
        db.commit()
        db.refresh(admin)
        assert is_admin(db, admin.id) == True
        
        # 创建admin角色
        admin2 = create_test_user(db, "admin2_admin_test", "admin")
        db.commit()
        db.refresh(admin2)
        assert is_admin(db, admin2.id) == True
        
    finally:
        db.close()


def test_admin_owns_all():
    """测试管理员可以访问所有内容"""
    db = TestingSessionLocal()
    try:
        # 创建教师和资源
        teacher = create_test_user(db, "teacher_resource", "teacher")
        cls = ClassGroup(name="测试班级", created_by=teacher.id)
        db.add(cls)
        db.commit()
        student = create_test_user(db, "student_resource", "student")
        db.add(ClassMember(class_id=cls.id, user_id=student.id))
        db.commit()
        q = create_test_question(db, created_by=teacher.id)
        
        # 创建管理员
        admin = create_test_user(db, "admin_test_own", "teacher")
        admin.is_admin = True
        db.commit()
        db.refresh(admin)
        
        # 验证管理员可以访问所有内容
        assert teacher_owns_student(db, admin.id, student.id) == True
        assert teacher_owns_class(db, admin.id, cls.id) == True
        assert teacher_owns_question(db, admin.id, q.id) == True
        
    finally:
        db.close()
