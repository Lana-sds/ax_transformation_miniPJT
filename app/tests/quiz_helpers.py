"""세트·복습·API 테스트용 DB 헬퍼. 풀, 세트, 풀이, 복습 항목을 직접 넣는다."""

import json

from conftest import make_question
from quiz import store
from quiz.pool import current_pool, freeze

PREFIX = "b20261105-99"


def qid(no: int) -> str:
    return f"{PREFIX}-{no:03d}"


def make_pool(conn, n: int) -> list[str]:
    ids = [qid(i) for i in range(1, n + 1)]
    for q in ids:
        make_question(conn, q)
    freeze(conn)
    conn.commit()
    return ids


def make_variant(conn, original: str, no: int, status: str = "passed") -> str:
    """원래 문제의 변형 문제. 풀 스냅샷에는 넣지 않는다(freeze는 variant_of가 있는 문제를 뺀다)."""
    vid = f"b20261105-98-{no:03d}"
    if not conn.execute("SELECT 1 FROM batches WHERE batch_id = 'b20261105-98'").fetchone():
        store.insert_batch(conn, "b20261105-98", "variant", "gen", "judge")
    store.upsert_question(
        conn, vid, "b20261105-98",
        {"bucket": "langgraph_basics", "topic": "t", "format": "single", "question_type": "concept",
         "variant_of": original},
        {"stem_en": "Variant?", "choices": [{"id": c, "text": c} for c in "ABCD"], "answer_key": ["B"],
         "explanation_ko": "해설", "segments": [{"segment_id": "s1", "en": "Variant?", "ko": "변형?"}],
         "grounding_records": [{"page": "/p", "quote": "q" * 40, "answer_basis": "근거"}], "cca_f_tag": "n/a"},
        status=status, drop_reason=None if status != "dropped" else "duplicate", regen_count=0,
        fetched_at="2026-11-05",
    )
    conn.commit()
    return vid


def add_set(conn, set_no: int, question_ids: list[str]) -> str:
    set_id = f"s{set_no:03d}-test"
    conn.execute(
        "INSERT INTO quiz_sets (set_id, set_no, pool_snapshot_id, question_ids_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (set_id, set_no, current_pool(conn), json.dumps(question_ids), "2026-11-05T00:00:00Z"),
    )
    conn.commit()
    return set_id


def add_attempt(conn, set_id: str, question_id: str, correct: bool, ts: str = "2026-11-05T00:00:00Z",
                tag: str | None = None, segment: str | None = None) -> int:
    cur = conn.execute(
        """INSERT INTO attempts (question_id, set_id, ts, answer, correct, mistake_tag, confused_segment_id, schema_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, 2)""",
        (question_id, set_id, ts, json.dumps(["B" if correct else "A"]), int(correct), tag, segment),
    )
    conn.commit()
    return cur.lastrowid


def add_review(conn, question_id: str, round_: int, due: int, state: str = "pending", tag: str = "reading") -> None:
    conn.execute(
        "INSERT INTO review_items (question_id, mistake_tag, review_round, due_set_no, state) VALUES (?, ?, ?, ?, ?)",
        (question_id, tag, round_, due, state),
    )
    conn.commit()


def review_row(conn, question_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM review_items WHERE question_id = ?", (question_id,)).fetchone()
    return dict(row) if row else None
