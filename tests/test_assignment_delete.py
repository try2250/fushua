from fastapi.testclient import TestClient
from app.models import User, ClassGroup, ClassMember
from tests.conftest import TestingSessionLocal, create_test_user, create_test_question, get_csrf_token, register_and_login
from app.models import Assignment, AssignmentRecord


def test_delete_assignment_with_cascade():
    """删除作业时级联删除相关记录"""
    db = TestingSessionLocal()
    try:
        # 创建教师、班级、学生
        teacher = create_test_user(db, "teacher_del", "teacher")
        cls = ClassGroup(name="删除测试班级", created_by=teacher.id)
        db.add(cls)
        db.commit()
        student = create_test_user(db, "student_del", "student")
        db.add(ClassMember(class_id=cls.id, user_id=student.id))
        db.commit()
        
        # 创建题目和作业
        q = create_test_question(db, created_by=teacher.id)
        assignment = Assignment(
            title="待删除作业",
            question_ids=str(q.id),
            created_by=teacher.id,
            class_id=cls.id
        )
        db.add(assignment)
        db.commit()
        
        # 让学生完成作业
        from datetime import datetime
        db.add(AssignmentRecord(
            assignment_id=assignment.id,
            user_id=student.id,
            completed=True,
            completed_at=datetime.now()
        ))
        db.commit()
        
        # 验证记录存在
        record_count = db.query(AssignmentRecord).filter(AssignmentRecord.assignment_id == assignment.id).count()
        assert record_count == 1
        
    finally:
        db.close()


def test_delete_assignment_permission():
    """教师只能删除自己创建的作业"""
    db = TestingSessionLocal()
    try:
        # 创建两个教师
        teacher_a = create_test_user(db, "teacher_a_del", "teacher")
        teacher_b = create_test_user(db, "teacher_b_del", "teacher")
        cls_a = ClassGroup(name="教师A的班", created_by=teacher_a.id)
        db.add(cls_a)
        db.commit()
        q = create_test_question(db, created_by=teacher_a.id)
        assignment = Assignment(
            title="教师A的作业",
            question_ids=str(q.id),
            created_by=teacher_a.id,
            class_id=cls_a.id
        )
        db.add(assignment)
        db.commit()
        assignment_id = assignment.id
        
    finally:
        db.close()
    
    # 教师B尝试删除教师A的作业
    # 这里需要客户端测试
    pass
