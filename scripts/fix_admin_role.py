"""
检查和修复管理员账号角色

使用方法：
python scripts/fix_admin_role.py
"""
import sys
import os

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User


def check_and_fix_admin():
    """检查并修复管理员账号"""
    db = SessionLocal()

    try:
        # 查找用户名为admin的账号
        admin_user = db.query(User).filter(User.username == "admin").first()

        if not admin_user:
            print("[ERROR] 未找到用户名为'admin'的账号")
            print("\n请提供管理员账号的用户名：")
            return

        print(f"[OK] 找到账号：{admin_user.username}")
        print(f"  - ID: {admin_user.id}")
        print(f"  - 显示名称: {admin_user.display_name}")
        print(f"  - 当前角色: {admin_user.role}")
        print(f"  - 是否禁用: {admin_user.is_disabled}")

        if admin_user.role != "admin":
            print(f"\n[WARNING] 角色不正确，当前为: {admin_user.role}")
            print("正在修复为: admin")

            admin_user.role = "admin"
            db.commit()

            print("[SUCCESS] 角色已修复为 admin")
        else:
            print("\n[OK] 角色正确，无需修复")

        if admin_user.is_disabled:
            print("\n[WARNING] 账号已被禁用")
            print("正在启用账号...")

            admin_user.is_disabled = False
            db.commit()

            print("[SUCCESS] 账号已启用")

        print("\n" + "="*50)
        print("管理员账号信息：")
        print(f"用户名: {admin_user.username}")
        print(f"角色: {admin_user.role}")
        print(f"状态: {'正常' if not admin_user.is_disabled else '已禁用'}")
        print("="*50)

    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        db.rollback()
    finally:
        db.close()


def list_all_admins():
    """列出所有管理员账号"""
    db = SessionLocal()

    try:
        admins = db.query(User).filter(User.role == "admin").all()

        print("\n所有管理员账号：")
        print("="*50)

        if not admins:
            print("未找到任何管理员账号")
        else:
            for admin in admins:
                status = "正常" if not admin.is_disabled else "已禁用"
                print(f"- {admin.username} (ID: {admin.id}, 状态: {status})")

        print("="*50)

    finally:
        db.close()


if __name__ == "__main__":
    print("管理员账号检查工具")
    print("="*50)

    check_and_fix_admin()
    list_all_admins()

    print("\n[SUCCESS] 检查完成！")
    print("\n如果问题仍然存在，请：")
    print("1. 退出登录")
    print("2. 重新登录")
    print("3. 访问 /admin/announcements")
