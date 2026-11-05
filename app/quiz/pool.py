"""풀 스냅샷 고정(design.md 5.2, US-3.1)."""

import hashlib
import sqlite3

from quiz.store import now


def pool_snapshot_id(question_ids: list[str]) -> str:
    return "ps_" + hashlib.sha256("\n".join(sorted(question_ids)).encode("utf-8")).hexdigest()[:12]


def freeze(conn: sqlite3.Connection) -> tuple[str, int]:
    """현재 passed 문제(변형 제외)로 풀 스냅샷을 만든다. 같은 문제 집합이면 같은 ID다."""
    ids = [r[0] for r in conn.execute(
        "SELECT question_id FROM questions WHERE status = 'passed' AND variant_of IS NULL"
    )]
    if not ids:
        raise RuntimeError("no passed questions to freeze")
    psid = pool_snapshot_id(ids)
    conn.execute("INSERT OR IGNORE INTO pool_snapshots (pool_snapshot_id, created_at) VALUES (?, ?)", (psid, now()))
    conn.executemany(
        "INSERT OR IGNORE INTO pool_snapshot_items (pool_snapshot_id, question_id) VALUES (?, ?)",
        [(psid, qid) for qid in ids],
    )
    return psid, len(ids)


def current_pool(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT pool_snapshot_id FROM pool_snapshots ORDER BY created_at DESC, rowid DESC LIMIT 1").fetchone()
    return row[0] if row else None
