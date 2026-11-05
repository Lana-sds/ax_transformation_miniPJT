"""SQLite 백업(design.md 8.4, US-0.2).

마이그레이션과 배치 전에 `sqlite3` backup API로 `data/backups/`에 복사한다.
최근 `KEEP`개만 남긴다. DB 파일이 없으면 백업하지 않는다.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from quiz import db

KEEP = 10


def backup_dir() -> Path:
    """DB 파일 옆 `backups/`. 기본 DB면 `data/backups/`다."""
    return db.db_path().parent / "backups"


def backup(src: Path, label: str, dest: Path | None = None, keep: int = KEEP,
           stamp: str | None = None) -> Path | None:
    if not src.exists():
        return None
    dest = dest or backup_dir()
    dest.mkdir(parents=True, exist_ok=True)
    stamp = stamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = dest / f"quiz-{stamp}-{label}.db"
    s, t = sqlite3.connect(src), sqlite3.connect(target)
    try:
        s.backup(t)
    finally:
        s.close()
        t.close()
    for old in sorted(dest.glob("quiz-*.db"))[:-keep]:
        old.unlink()
    return target
