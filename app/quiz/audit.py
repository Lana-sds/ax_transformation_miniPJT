"""감사 표본과 결과(design.md 6.6, FR-9, requirements 7.2).

- 시드: `int(sha256(pool_snapshot_id)[:16], 16)`. 표본: `random.Random(seed).sample(sorted(ids), 20)`.
- 같은 풀 스냅샷이면 기존 감사를 돌려준다. `audit_id`는 `"au_" + pool_snapshot_id`의 해시 부분이다.
- 표본 20문항의 기록이 모두 차면 `result`를 계산한다. 다시 기록하면 다시 계산한다.
- `audit_failed` 전환과 재감사는 T5.6에서 한다.
"""

import hashlib
import json
import random
import sqlite3

from quiz.pool import current_pool
from quiz.store import now

SAMPLE_SIZE = 20
FLAGS = ("answer_key_error", "quote_unsupported", "mapping_unfaithful")
# requirements 7.2: 판정별 허용 문항 수
LIMITS = {"answer_key_error": 1, "quote_unsupported": 2, "mapping_unfaithful": 2}


class NoPool(Exception):
    pass


class PoolTooSmall(Exception):
    pass


class NotInSample(Exception):
    pass


class AuditNotFound(Exception):
    pass


def seed_for(pool_snapshot_id: str) -> int:
    return int(hashlib.sha256(pool_snapshot_id.encode("utf-8")).hexdigest()[:16], 16)


def audit_id_for(pool_snapshot_id: str) -> str:
    return "au_" + pool_snapshot_id.removeprefix("ps_")


def judge(records: list[dict]) -> str:
    counts = {k: sum(1 for r in records if r[k]) for k in FLAGS}
    return "pass" if all(counts[k] <= LIMITS[k] for k in FLAGS) else "fail"


def create(conn: sqlite3.Connection) -> dict:
    """현재 풀 스냅샷의 감사를 만든다. 이미 있으면 그것을 돌려준다."""
    psid = current_pool(conn)
    if psid is None:
        raise NoPool()
    row = conn.execute("SELECT audit_id FROM audits WHERE pool_snapshot_id = ?", (psid,)).fetchone()
    if row:
        return get(conn, row[0])
    ids = sorted(r[0] for r in conn.execute(
        "SELECT question_id FROM pool_snapshot_items WHERE pool_snapshot_id = ?", (psid,)))
    if len(ids) < SAMPLE_SIZE:
        raise PoolTooSmall(len(ids))
    seed = seed_for(psid)
    sample = random.Random(seed).sample(ids, SAMPLE_SIZE)
    aid = audit_id_for(psid)
    conn.execute(
        "INSERT INTO audits (audit_id, pool_snapshot_id, seed, sample_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (aid, psid, str(seed), json.dumps(sample), now()),
    )
    conn.commit()
    return get(conn, aid)


def current(conn: sqlite3.Connection) -> dict | None:
    psid = current_pool(conn)
    if psid is None:
        return None
    row = conn.execute("SELECT audit_id FROM audits WHERE pool_snapshot_id = ?", (psid,)).fetchone()
    return get(conn, row[0]) if row else None


def get(conn: sqlite3.Connection, audit_id: str) -> dict:
    row = conn.execute(
        "SELECT audit_id, pool_snapshot_id, seed, sample_json, created_at, result FROM audits WHERE audit_id = ?",
        (audit_id,),
    ).fetchone()
    if row is None:
        raise AuditNotFound(audit_id)
    records = {
        r[0]: {"answer_key_error": bool(r[1]), "quote_unsupported": bool(r[2]), "mapping_unfaithful": bool(r[3]),
               "note": r[4], "recorded_at": r[5]}
        for r in conn.execute(
            "SELECT question_id, answer_key_error, quote_unsupported, mapping_unfaithful, note, recorded_at"
            " FROM audit_records WHERE audit_id = ?", (audit_id,))
    }
    return {
        "audit_id": row[0], "pool_snapshot_id": row[1], "seed": row[2], "sample": json.loads(row[3]),
        "created_at": row[4], "result": row[5], "records": records,
    }


def record(conn: sqlite3.Connection, audit_id: str, question_id: str, *, answer_key_error: bool,
           quote_unsupported: bool, mapping_unfaithful: bool, note: str | None = None) -> dict:
    """문항 하나의 감사 결과를 저장한다. 표본이 모두 차면 `result`를 계산한다."""
    a = get(conn, audit_id)
    if question_id not in a["sample"]:
        raise NotInSample(question_id)
    conn.execute(
        """INSERT INTO audit_records (audit_id, question_id, answer_key_error, quote_unsupported,
               mapping_unfaithful, note, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (audit_id, question_id) DO UPDATE SET
               answer_key_error = excluded.answer_key_error, quote_unsupported = excluded.quote_unsupported,
               mapping_unfaithful = excluded.mapping_unfaithful, note = excluded.note,
               recorded_at = excluded.recorded_at""",
        (audit_id, question_id, int(answer_key_error), int(quote_unsupported), int(mapping_unfaithful), note, now()),
    )
    a = get(conn, audit_id)
    result = judge(list(a["records"].values())) if len(a["records"]) == len(a["sample"]) else None
    conn.execute("UPDATE audits SET result = ? WHERE audit_id = ?", (result, audit_id))
    conn.commit()
    a["result"] = result
    return a
