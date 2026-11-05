"""번호 붙은 SQL 마이그레이션 적용(design.md 8.4).

파일 이름은 `NNNN_<이름>.sql`이고 번호가 schema_version이다.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from quiz.db import MIGRATIONS_DIR


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def migration_files(directory: Path = MIGRATIONS_DIR) -> list[tuple[int, Path]]:
    files = []
    for path in sorted(directory.glob("*.sql")):
        files.append((int(path.name.split("_", 1)[0]), path))
    return files


def pending_migrations(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[int]:
    """아직 적용하지 않은 마이그레이션 번호."""
    version = current_version(conn)
    return [v for v, _ in migration_files(directory) if v > version]


def current_version(conn: sqlite3.Connection) -> int:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_version'"
    ).fetchone()
    if not exists:
        return 0
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def apply_migrations(conn: sqlite3.Connection, directory: Path = MIGRATIONS_DIR) -> list[int]:
    """미적용 마이그레이션을 순서대로 적용하고 적용한 번호 목록을 돌려준다."""
    applied = []
    for version, path in migration_files(directory):
        if version <= current_version(conn):
            continue
        sql = path.read_text(encoding="utf-8")
        conn.executescript(
            "BEGIN;\n"
            + sql
            + f"\nINSERT INTO schema_version (version, applied_at) VALUES ({version}, '{_now()}');\nCOMMIT;"
        )
        applied.append(version)
    return applied
