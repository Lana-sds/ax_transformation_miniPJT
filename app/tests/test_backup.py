import shutil
import sqlite3

from fastapi.testclient import TestClient

from quiz import backup, cli, db
from quiz.migrate import apply_migrations, current_version, migration_files
from quiz.server import app


def _tables(path):
    with sqlite3.connect(path) as c:
        return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def test_migrate_creates_backup_with_same_tables(tmp_path, monkeypatch):
    db_file = tmp_path / "quiz.db"
    monkeypatch.setenv("QUIZ_DB", str(db_file))
    assert cli.main(["migrate"]) == 0  # 빈 DB: 백업할 것이 없다
    assert not list((tmp_path / "backups").glob("*.db"))
    assert cli.main(["migrate"]) == 0
    files = list((tmp_path / "backups").glob("*.db"))
    assert len(files) == 1
    assert _tables(files[0]) == _tables(db_file)
    assert "questions" in _tables(files[0])


def test_backup_keeps_latest_n(tmp_path):
    db_file = tmp_path / "quiz.db"
    sqlite3.connect(db_file).execute("CREATE TABLE t (x)").connection.commit()
    dest = tmp_path / "backups"
    made = [backup.backup(db_file, "test", dest=dest, keep=3, stamp=f"20261105T0000{i:02d}Z") for i in range(5)]
    left = sorted(p.name for p in dest.glob("*.db"))
    assert left == sorted(p.name for p in made[-3:])


def test_backup_skips_missing_db(tmp_path):
    assert backup.backup(tmp_path / "none.db", "x", dest=tmp_path / "b") is None


def _db_at_first_migration(tmp_path, monkeypatch):
    """0001만 적용한 DB. 서버가 시작할 때 0002 이후가 대기 중이다."""
    db_file = tmp_path / "quiz.db"
    monkeypatch.setenv("QUIZ_DB", str(db_file))
    first = tmp_path / "first"
    first.mkdir()
    shutil.copy(migration_files()[0][1], first)
    with db.connect(db_file) as conn:
        apply_migrations(conn, directory=first)
    return db_file


def test_server_start_backs_up_before_pending_migration(tmp_path, monkeypatch):
    db_file = _db_at_first_migration(tmp_path, monkeypatch)
    with TestClient(app):
        pass
    files = list((tmp_path / "backups").glob("quiz-*-migrate.db"))
    assert len(files) == 1
    with sqlite3.connect(files[0]) as c:  # 백업은 마이그레이션 전 상태다
        assert current_version(c) == 1
    with sqlite3.connect(db_file) as c:
        assert current_version(c) == migration_files()[-1][0]


def test_server_start_without_pending_migration_makes_no_backup(tmp_path, monkeypatch):
    db_file = tmp_path / "quiz.db"
    monkeypatch.setenv("QUIZ_DB", str(db_file))
    with db.connect(db_file) as conn:
        apply_migrations(conn)
    with TestClient(app):
        pass
    assert not list((tmp_path / "backups").glob("*.db"))
