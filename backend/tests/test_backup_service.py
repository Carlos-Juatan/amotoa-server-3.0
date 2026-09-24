import pytest
import os
import time
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.backup_service import BackupService

@pytest.fixture
def mock_backup_dir(tmp_path):
    with patch("src.services.backup_service.BackupService.BACKUP_DIR", str(tmp_path)):
        yield tmp_path

@pytest.mark.asyncio
async def test_create_backup(mock_backup_dir):
    # Mock the subprocess shell
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch("asyncio.create_subprocess_shell", return_value=mock_process) as mock_shell:
        filename = await BackupService.create_backup()
        
        assert filename.startswith("backup_")
        assert filename.endswith(".gz")
        mock_shell.assert_called_once()
        cmd = mock_shell.call_args[0][0]
        assert "mongodump" in cmd
        assert "--archive" in cmd
        assert "--gzip" in cmd

def test_list_backups(mock_backup_dir):
    # Create some dummy backup files
    file1 = mock_backup_dir / "backup_1.gz"
    file1.write_text("data")
    file2 = mock_backup_dir / "backup_2.gz"
    file2.write_text("data2")
    
    backups = BackupService.list_backups()
    assert len(backups) == 2
    filenames = [b["filename"] for b in backups]
    assert "backup_1.gz" in filenames
    assert "backup_2.gz" in filenames

def test_prune_old_backups(mock_backup_dir):
    # Create an old backup file and a new one
    old_file = mock_backup_dir / "backup_old.gz"
    old_file.write_text("old")
    # Set modify time to 15 days ago
    old_time = time.time() - (15 * 86400)
    os.utime(old_file, (old_time, old_time))

    new_file = mock_backup_dir / "backup_new.gz"
    new_file.write_text("new")

    BackupService.prune_old_backups(retention_days=14)

    assert not old_file.exists()
    assert new_file.exists()
