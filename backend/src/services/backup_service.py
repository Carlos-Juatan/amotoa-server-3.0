import os
import glob
import time
import asyncio
from datetime import datetime, timedelta
from src.core.config import settings

class BackupService:
    BACKUP_DIR = "/tmp/backups" # Adjust as needed, usually from settings

    @classmethod
    def get_backup_dir(cls):
        os.makedirs(cls.BACKUP_DIR, exist_ok=True)
        return cls.BACKUP_DIR

    @classmethod
    async def create_backup(cls) -> str:
        """Create a compressed MongoDB backup using mongodump."""
        backup_dir = cls.get_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.gz"
        filepath = os.path.join(backup_dir, filename)

        # Build mongodump command
        # Use settings.MONGODB_URI
        uri = settings.MONGODB_URI
        cmd = f"mongodump --uri=\"{uri}\" --archive=\"{filepath}\" --gzip"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Backup failed: {stderr.decode()}")
        
        # Cleanup old backups
        cls.prune_old_backups()

        return filename

    @classmethod
    def list_backups(cls) -> list[dict]:
        backup_dir = cls.get_backup_dir()
        backups = []
        for file in glob.glob(os.path.join(backup_dir, "*.gz")):
            stat = os.stat(file)
            backups.append({
                "filename": os.path.basename(file),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime)
            })
        # Sort by newest first
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    @classmethod
    def prune_old_backups(cls, retention_days: int = 14):
        """Delete backups older than retention_days."""
        backup_dir = cls.get_backup_dir()
        now = time.time()
        cutoff = now - (retention_days * 86400)

        for file in glob.glob(os.path.join(backup_dir, "*.gz")):
            if os.stat(file).st_mtime < cutoff:
                try:
                    os.remove(file)
                except Exception:
                    pass
