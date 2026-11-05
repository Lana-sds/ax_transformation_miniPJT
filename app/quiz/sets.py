"""세트 구성(design.md 6.3, FR-1).

한 세트는 항상 10문제다. 채우는 순서:
1. 기한이 된 복습 문제 최대 3개(`due_set_no`가 이른 순, 같으면 question_id 순). 나머지는 다음 세트로 넘긴다.
   개념 실수는 통과한 변형 문제가 있으면 그것을 낸다(`review.served_question`).
2. 남은 새 문제(한 번도 풀지 않은 풀 문제). 버킷·형식을 따지지 않고 무작위다.
3. 새 문제가 소진되면, 맞힌 적이 있고 복습 큐(`pending`)에 없는 문제를 마지막 풀이가 오래된 순으로. 같은 시각이면 무작위다.
`retired` 문제는 다시 내지 않는다. 문제는 현재 풀 스냅샷 안에서만 고른다.
10개를 채우지 못하면 세트를 만들지 않는다(M0 임시 규칙 제거).
"""

import json
import random
import sqlite3
import uuid

from quiz import review
from quiz.pool import current_pool
from quiz.store import now

SET_SIZE = 10
MAX_REVIEW = 3


class NoPoolError(RuntimeError):
    pass


class PoolTooSmallError(RuntimeError):
    pass


def _pool_ids(conn: sqlite3.Connection, psid: str) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT question_id FROM pool_snapshot_items WHERE pool_snapshot_id = ? ORDER BY question_id", (psid,)
    )]


def due_reviews(conn: sqlite3.Connection, set_no: int, pool: set[str]) -> list[sqlite3.Row]:
    """기한이 된 pending 복습 항목. 이른 순이고 현재 풀에 있는 원래 문제만이다."""
    rows = conn.execute(
        """SELECT * FROM review_items WHERE state = 'pending' AND due_set_no <= ?
           ORDER BY due_set_no, question_id""",
        (set_no,),
    ).fetchall()
    return [r for r in rows if r["question_id"] in pool]


def compose(conn: sqlite3.Connection, set_no: int, rng: random.Random | None = None) -> list[str]:
    rng = rng or random.Random()
    psid = current_pool(conn)
    if psid is None:
        raise NoPoolError("no frozen pool snapshot")
    pool_list = _pool_ids(conn, psid)
    pool = set(pool_list)

    chosen = [review.served_question(conn, item) for item in due_reviews(conn, set_no, pool)[:MAX_REVIEW]]

    attempted = {r[0] for r in conn.execute("SELECT DISTINCT question_id FROM attempts")}
    fresh = [q for q in pool_list if q not in attempted and q not in chosen]
    need = SET_SIZE - len(chosen)
    chosen += rng.sample(fresh, min(need, len(fresh)))

    if len(chosen) < SET_SIZE:
        queued = {r[0] for r in conn.execute(
            "SELECT question_id FROM review_items WHERE state IN ('pending', 'retired')"
        )}
        # 원래 문제 기준으로 모은다. 변형 문제 풀이는 원래 문제의 기록으로 센다.
        stats = conn.execute(
            """SELECT COALESCE(q.variant_of, a.question_id) AS original, MAX(a.ts) AS last_ts, MAX(a.correct) AS ever
               FROM attempts a JOIN questions q ON q.question_id = a.question_id
               GROUP BY original"""
        ).fetchall()
        candidates = [
            (r["last_ts"], r["original"]) for r in stats
            if r["ever"] and r["original"] in pool and r["original"] not in queued and r["original"] not in chosen
        ]
        rng.shuffle(candidates)
        candidates.sort(key=lambda c: c[0])  # 안정 정렬이라 같은 시각은 섞인 순서가 남는다
        chosen += [q for _, q in candidates[: SET_SIZE - len(chosen)]]

    if len(chosen) < SET_SIZE:
        raise PoolTooSmallError(f"only {len(chosen)} questions available for set {set_no}, need {SET_SIZE}")
    return chosen


def review_status(conn: sqlite3.Connection, set_no: int, question_ids: list[str]) -> dict[str, str | None]:
    """문제마다 이전 세트(set_no 미만) 기록. 오답이 있으면 "wrong", 정답만 있으면 "seen", 없으면 None(T4.8).

    변형 문제는 원래 문제의 기록으로 센다.
    """
    rows = conn.execute(
        """SELECT COALESCE(q.variant_of, a.question_id) AS original, MIN(a.correct) AS all_correct
           FROM attempts a
           JOIN questions q ON q.question_id = a.question_id
           JOIN quiz_sets s ON s.set_id = a.set_id
           WHERE s.set_no < ?
           GROUP BY original""",
        (set_no,),
    ).fetchall()
    seen = {r["original"]: ("seen" if r["all_correct"] else "wrong") for r in rows}
    return {q: seen.get(review.original_of(conn, q)) for q in question_ids}


def latest_set(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM quiz_sets ORDER BY set_no DESC LIMIT 1").fetchone()


def untagged_wrong(conn: sqlite3.Connection, set_id: str) -> list[int]:
    """세트에서 태그 없는 오답 행의 attempt_id(design.md 8.6)."""
    return [r[0] for r in conn.execute(
        "SELECT attempt_id FROM attempts WHERE set_id = ? AND correct = 0 AND mistake_tag IS NULL ORDER BY attempt_id",
        (set_id,),
    )]


def create(conn: sqlite3.Connection, rng: random.Random | None = None) -> dict:
    """다음 번호로 세트를 만들어 저장한다. 직전 세트 태그 확인은 호출하는 쪽(API)이 한다."""
    psid = current_pool(conn)
    if psid is None:
        raise NoPoolError("no frozen pool snapshot")
    prev = latest_set(conn)
    set_no = (prev["set_no"] if prev else 0) + 1
    chosen = compose(conn, set_no, rng)
    set_id = f"s{set_no:03d}-{uuid.uuid4().hex[:8]}"
    conn.execute(
        "INSERT INTO quiz_sets (set_id, set_no, pool_snapshot_id, question_ids_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (set_id, set_no, psid, json.dumps(chosen), now()),
    )
    return {"set_id": set_id, "set_no": set_no, "question_ids": chosen}
