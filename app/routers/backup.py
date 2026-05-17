import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.database import get_db
from app.models import BackupLog
from app.services.backup_service import BackupService
from app.auth import require_admin_role
from app.security import validate_csrf_async

router = APIRouter()

BACKUP_SECRET = os.getenv("BACKUP_SECRET", "")


def require_admin(request: Request, db: Session):
    """验证管理员权限"""
    user_id = require_admin_role(request, db)
    from app.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


@router.post("/admin/backup/trigger")
async def trigger_backup(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    x_backup_secret: Optional[str] = Header(None)
):
    """
    触发备份（供 Cron Job 或管理员调用）

    需要 X-Backup-Secret header 认证
    """
    # 验证密钥
    if not BACKUP_SECRET:
        raise HTTPException(status_code=500, detail="BACKUP_SECRET 未配置")

    if x_backup_secret != BACKUP_SECRET:
        raise HTTPException(status_code=401, detail="无效的备份密钥")

    # 判断触发来源
    triggered_by = "cron"
    try:
        # 尝试获取当前用户，如果成功则是管理员触发
        user_id = require_admin_role(request, db)
        if user_id:
            triggered_by = "admin"
    except:
        pass

    # 执行备份
    service = BackupService(db)
    try:
        result = service.trigger_backup(triggered_by=triggered_by)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")


@router.get("/admin/backup")
async def backup_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    """备份管理页面"""
    require_admin(request, db)

    # 获取备份列表
    backups = db.query(BackupLog).order_by(BackupLog.created_at.desc()).limit(50).all()

    # 获取统计信息
    service = BackupService(db)
    stats = service.get_backup_stats()

    return request.app.state.templates.TemplateResponse(
        "admin/backup.html",
        {
            "request": request,
            "backups": backups,
            "stats": stats,
            "csrf_token": request.session.get("csrf_token", ""),
        },
    )


@router.get("/admin/backup/logs")
async def get_backup_logs(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 20
):
    """获取备份列表（JSON）"""
    require_admin(request, db)

    offset = (page - 1) * page_size
    backups = db.query(BackupLog).order_by(
        BackupLog.created_at.desc()
    ).offset(offset).limit(page_size).all()

    total = db.query(BackupLog).count()

    return {
        "backups": [
            {
                "id": b.id,
                "created_at": b.created_at.isoformat(),
                "status": b.status,
                "file_path": b.file_path,
                "file_size": b.file_size,
                "triggered_by": b.triggered_by,
                "duration_seconds": b.duration_seconds,
                "error_message": b.error_message
            }
            for b in backups
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/admin/backup/stats")
async def get_backup_stats(request: Request, db: Annotated[Session, Depends(get_db)]):
    """获取备份统计信息"""
    require_admin(request, db)

    service = BackupService(db)
    stats = service.get_backup_stats()

    return stats


@router.get("/admin/backup/download/{backup_id}")
async def download_backup(
    request: Request,
    backup_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """下载备份文件"""
    require_admin(request, db)

    # 查询备份记录
    backup = db.query(BackupLog).filter(BackupLog.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份记录不存在")

    if not backup.file_path:
        raise HTTPException(status_code=404, detail="备份文件路径为空")

    # 构建文件路径
    backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
    file_path = backup_dir / backup.file_path

    # 安全检查：防止路径遍历
    try:
        file_path = file_path.resolve()
        backup_dir = backup_dir.resolve()
        if not str(file_path).startswith(str(backup_dir)):
            raise HTTPException(status_code=403, detail="非法的文件路径")
    except Exception:
        raise HTTPException(status_code=403, detail="非法的文件路径")

    # 检查文件是否存在
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")

    # 返回文件
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.post("/admin/backup/delete/{backup_id}")
async def delete_backup(
    request: Request,
    backup_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """删除备份"""
    require_admin(request, db)

    # 验证 CSRF
    await validate_csrf_async(request)

    # 查询备份记录
    backup = db.query(BackupLog).filter(BackupLog.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份记录不存在")

    # 删除文件
    if backup.file_path:
        backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
        file_path = backup_dir / backup.file_path
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

    # 删除数据库记录
    db.delete(backup)
    db.commit()

    return {"status": "success", "message": "备份已删除"}


@router.post("/admin/backup/validate/{backup_id}")
async def validate_backup(
    request: Request,
    backup_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """验证备份完整性"""
    require_admin(request, db)

    service = BackupService(db)
    result = service.validate_backup(backup_id)

    return result


@router.post("/admin/backup/cleanup")
async def cleanup_backups(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    keep_days: int = 30
):
    """清理旧备份"""
    require_admin(request, db)

    # 验证 CSRF
    await validate_csrf_async(request)

    service = BackupService(db)
    result = service.cleanup_old_backups(keep_days=keep_days)

    return result
