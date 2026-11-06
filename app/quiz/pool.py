"""풀 스냅샷 고정(design.md 5.2, US-3.1)."""

import hashlib
import sqlite3

from quiz.store import now


def pool_snapshot_id(question_ids: list[str]) -> str:
    return "ps_" + hashlib.sha256("\n".join(sorted(question_ids)).encode("utf-8")).hexdigest()[:12]


def freeze(conn: sqlite3.Connection) -> tuple[str, int]:
    """현재 passed 문제(변형 제외)로 풀 스냅샷을 만든다. 같은 문제 집합이면 같은 ID다.

    돌려준 스냅샷이 현재 풀(`current_pool`)이 된다. `audit_failed` 문제는 passed가 아니라 들어가지 않는다.
    """
    ids = [r[0] for r in conn.execute(
        "SELECT question_id FROM questions WHERE status = 'passed' AND variant_of IS NULL"
    )]
    if not ids:
        raise RuntimeError("no passed questions to freeze")
    psid = pool_snapshot_id(ids)
    if current_pool(conn) == psid:
        return psid, len(ids)
    exists = conn.execute("SELECT 1 FROM pool_snapshots WHERE pool_snapshot_id = ?", (psid,)).fetchone()
    if exists:
        # 예전에 고정한 집합으로 돌아왔다(예: 감사에서 빠진 문제를 뺀 결과). 마지막 고정이 현재 풀이 되도록
        # 시각을 지금으로 바꾸고 rowid를 맨 뒤로 옮긴다. 같은 초에 고정한 스냅샷과는 rowid로 가른다
        conn.execute(
            "UPDATE pool_snapshots SET created_at = ?, rowid = (SELECT MAX(rowid) + 1 FROM pool_snapshots)"
            " WHERE pool_snapshot_id = ?", (now(), psid),
        )
    else:
        conn.execute("INSERT INTO pool_snapshots (pool_snapshot_id, created_at) VALUES (?, ?)", (psid, now()))
    conn.executemany(
        "INSERT OR IGNORE INTO pool_snapshot_items (pool_snapshot_id, question_id) VALUES (?, ?)",
        [(psid, qid) for qid in ids],
    )
    return psid, len(ids)


def current_pool(conn: sqlite3.Connection) -> str | None:
    """마지막으로 고정한 풀 스냅샷. `freeze`가 돌려준 ID와 같다."""
    row = conn.execute("SELECT pool_snapshot_id FROM pool_snapshots ORDER BY created_at DESC, rowid DESC LIMIT 1").fetchone()
    return row[0] if row else None
