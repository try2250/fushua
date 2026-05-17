import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import BackupLog


class BackupService:
    """备份服务：处理数据库备份的触发、验证和管理"""

    def __init__(self, db: Session):
        self.db = db
        self.backup_script = Path("scripts/backup_db.sh")
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
        self.timeout = 300  # 5分钟超时

    def trigger_backup(self, triggered_by: str = "cron") -> Dict[str, Any]:
        """
        触发备份操作

        Args:
            triggered_by: 触发来源 ('cron', 'admin', 'manual')

        Returns:
            包含备份结果的字典
        """
        # 检查是否有正在运行的备份
        running_backups = self.db.query(BackupLog).filter(
            BackupLog.status == "running"
        ).count()

        if running_backups > 0:
            raise ValueError("已有备份任务正在运行，请稍后再试")

        # 清理僵尸状态（超过2小时的 running 状态）
        stale_threshold = datetime.utcnow() - timedelta(hours=2)
        stale_backups = self.db.query(BackupLog).filter(
            BackupLog.status == "running",
            BackupLog.created_at < stale_threshold
        ).all()

        for backup in stale_backups:
            backup.status = "failed"
            backup.error_message = "备份超时或进程异常终止"
            backup.duration_seconds = 7200  # 2小时

        if stale_backups:
            self.db.commit()

        # 创建备份记录
        backup_log = BackupLog(
            status="running",
            triggered_by=triggered_by
        )
        self.db.add(backup_log)
        self.db.commit()
        self.db.refresh(backup_log)

        start_time = time.time()

        try:
            # 检查脚本是否存在
            if not self.backup_script.exists():
                raise FileNotFoundError(f"备份脚本不存在: {self.backup_script}")

            # 检查必要的工具是否可用
            self._check_required_tools()

            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 执行备份脚本
            result = subprocess.run(
                ["bash", str(self.backup_script)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )

            # 解析输出获取备份文件路径
            file_path = self._extract_backup_path(result.stdout)

            if not file_path:
                raise ValueError("无法从脚本输出中提取备份文件路径")

            # 获取文件大小
            full_path = self.backup_dir / file_path
            file_size = full_path.stat().st_size if full_path.exists() else None

            # 更新备份记录
            duration = int(time.time() - start_time)
            backup_log.status = "success"
            backup_log.file_path = str(file_path)
            backup_log.file_size = file_size
            backup_log.duration_seconds = duration
            self.db.commit()

            return {
                "status": "success",
                "backup_id": backup_log.id,
                "file_path": str(file_path),
                "file_size": file_size,
                "duration_seconds": duration
            }

        except subprocess.TimeoutExpired:
            duration = int(time.time() - start_time)
            backup_log.status = "failed"
            backup_log.error_message = f"备份超时（超过 {self.timeout} 秒）"
            backup_log.duration_seconds = duration
            self.db.commit()
            raise

        except subprocess.CalledProcessError as e:
            duration = int(time.time() - start_time)
            backup_log.status = "failed"
            backup_log.error_message = f"备份脚本执行失败: {e.stderr}"
            backup_log.duration_seconds = duration
            self.db.commit()
            raise

        except Exception as e:
            duration = int(time.time() - start_time)
            backup_log.status = "failed"
            backup_log.error_message = str(e)
            backup_log.duration_seconds = duration
            self.db.commit()
            raise

    def _extract_backup_path(self, output: str) -> Optional[str]:
        """从脚本输出中提取备份文件路径"""
        # 首先查找 BACKUP_FILE_PATH= 格式
        for line in output.split("\n"):
            if "BACKUP_FILE_PATH=" in line:
                # 提取路径
                path = line.split("BACKUP_FILE_PATH=", 1)[1].strip()
                # 提取文件名（去掉目录部分）
                if "/" in path:
                    return path.split("/")[-1]
                return path

        # 兼容旧格式：查找包含 "fushua_" 的行
        for line in output.split("\n"):
            if "fushua_" in line and ("backups/" in line or self.backup_dir.name in line):
                # 提取文件名
                parts = line.split()
                for part in parts:
                    if "fushua_" in part:
                        # 提取相对路径
                        if "/" in part:
                            return part.split("/")[-1]
                        return part
        return None

    def _check_required_tools(self):
        """检查备份所需的工具是否可用"""
        # 检查 bash
        try:
            subprocess.run(["bash", "--version"], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("bash 不可用，无法执行备份脚本")

        # 检查数据库类型
        database_url = os.getenv("DATABASE_URL", "")

        if "postgresql" in database_url:
            # 检查 pg_dump
            try:
                subprocess.run(["pg_dump", "--version"], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError("pg_dump 不可用，无法备份 PostgreSQL 数据库。请联系管理员安装 postgresql-client")

            # 检查 gzip
            try:
                subprocess.run(["gzip", "--version"], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError("gzip 不可用，无法压缩备份文件")
        else:
            # 检查 sqlite3
            try:
                subprocess.run(["sqlite3", "--version"], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError("sqlite3 不可用，无法备份 SQLite 数据库")

    def validate_backup(self, backup_id: int) -> Dict[str, Any]:
        """
        验证备份文件完整性

        Args:
            backup_id: 备份记录 ID

        Returns:
            验证结果字典
        """
        backup_log = self.db.query(BackupLog).filter(BackupLog.id == backup_id).first()

        if not backup_log:
            return {
                "status": "error",
                "message": "备份记录不存在"
            }

        if not backup_log.file_path:
            return {
                "status": "error",
                "message": "备份文件路径为空"
            }

        file_path = self.backup_dir / backup_log.file_path
        checks = {
            "file_exists": False,
            "file_size_ok": False,
            "integrity_check": False
        }

        # 检查文件存在性
        if not file_path.exists():
            return {
                "status": "invalid",
                "checks": checks,
                "message": "备份文件不存在"
            }
        checks["file_exists"] = True

        # 检查文件大小
        actual_size = file_path.stat().st_size
        if actual_size < 100 * 1024:  # 小于 100KB 可能有问题
            return {
                "status": "invalid",
                "checks": checks,
                "message": f"备份文件过小: {actual_size} 字节"
            }
        checks["file_size_ok"] = True

        # 检查文件完整性
        try:
            if file_path.suffix == ".db":
                # SQLite 完整性检查
                result = subprocess.run(
                    ["sqlite3", str(file_path), "PRAGMA integrity_check;"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0 and "ok" in result.stdout.lower():
                    checks["integrity_check"] = True
            elif file_path.suffix == ".gz":
                # PostgreSQL 压缩文件测试
                result = subprocess.run(
                    ["gunzip", "-t", str(file_path)],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    checks["integrity_check"] = True
        except Exception as e:
            return {
                "status": "error",
                "checks": checks,
                "message": f"完整性检查失败: {str(e)}"
            }

        if all(checks.values()):
            return {
                "status": "valid",
                "checks": checks,
                "message": "备份文件完整"
            }
        else:
            return {
                "status": "invalid",
                "checks": checks,
                "message": "备份文件验证失败"
            }

    def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
        """
        清理旧备份

        Args:
            keep_days: 保留天数

        Returns:
            清理结果
        """
        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

        # 查询需要删除的备份
        old_backups = self.db.query(BackupLog).filter(
            BackupLog.created_at < cutoff_date,
            BackupLog.status == "success"
        ).all()

        deleted_count = 0
        deleted_size = 0

        for backup in old_backups:
            if backup.file_path:
                file_path = self.backup_dir / backup.file_path
                if file_path.exists():
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_size += file_size
                        deleted_count += 1
                    except Exception as e:
                        print(f"删除文件失败 {file_path}: {e}")

            # 删除数据库记录
            self.db.delete(backup)

        self.db.commit()

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "deleted_size_mb": round(deleted_size / (1024 * 1024), 2),
            "keep_days": keep_days
        }

    def get_backup_stats(self) -> Dict[str, Any]:
        """
        获取备份统计信息

        Returns:
            统计信息字典
        """
        total_backups = self.db.query(func.count(BackupLog.id)).scalar()
        success_count = self.db.query(func.count(BackupLog.id)).filter(
            BackupLog.status == "success"
        ).scalar()
        failed_count = self.db.query(func.count(BackupLog.id)).filter(
            BackupLog.status == "failed"
        ).scalar()

        total_size = self.db.query(func.sum(BackupLog.file_size)).filter(
            BackupLog.status == "success"
        ).scalar() or 0

        last_backup = self.db.query(BackupLog).order_by(
            desc(BackupLog.created_at)
        ).first()

        success_rate = success_count / total_backups if total_backups > 0 else 0

        return {
            "total_backups": total_backups,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_rate, 3),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "last_backup": {
                "created_at": last_backup.created_at.isoformat() if last_backup else None,
                "status": last_backup.status if last_backup else None,
                "file_size": last_backup.file_size if last_backup else None
            } if last_backup else None
        }

    def check_consecutive_failures(self, threshold: int = 3) -> bool:
        """
        检查是否有连续失败

        Args:
            threshold: 连续失败阈值

        Returns:
            是否达到阈值
        """
        recent_backups = self.db.query(BackupLog).order_by(
            desc(BackupLog.created_at)
        ).limit(threshold).all()

        if len(recent_backups) < threshold:
            return False

        return all(backup.status == "failed" for backup in recent_backups)
