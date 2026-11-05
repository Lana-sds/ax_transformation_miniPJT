"""SQLite 연결과 경로(design.md 3.2, 8.4)."""

import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "app"
DATA_DIR = REPO_ROOT / "data"
MIGRATIONS_DIR = APP_ROOT / "migrations"


def db_path() -> Path:
    """DB 파일 경로. 테스트는 `QUIZ_DB`로 바꾼다."""
    override = os.environ.get("QUIZ_DB")
    return Path(override) if override else DATA_DIR / "quiz.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
