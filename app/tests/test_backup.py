import sqlite3

from quiz import backup, cli


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
