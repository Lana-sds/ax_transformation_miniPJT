import json

import pytest

from quiz import db, store
from quiz.migrate import apply_migrations
from quiz.pool import freeze


def make_question(conn, qid: str, answer_key=("B",), fmt="single", batch_id="b20261105-99"):
    if not conn.execute("SELECT 1 FROM batches WHERE batch_id = ?", (batch_id,)).fetchone():
        store.insert_batch(conn, batch_id, "pool", "gen", "judge")
    store.upsert_question(
        conn, qid, batch_id,
        {"bucket": "langgraph_basics", "topic": "t", "format": fmt, "question_type": "concept"},
        {
            "stem_en": "What does StateGraph do?",
            "choices": [{"id": c, "text": f"choice {c}"} for c in "ABCD"],
            "answer_key": list(answer_key),
            "explanation_ko": "해설",
            "segments": [{"segment_id": "s1", "en": "What does StateGraph do?", "ko": "StateGraph는 무엇을 하나?"}],
            "grounding_records": [{"page": "/oss/python/langgraph/graph-api", "quote": "q" * 40, "answer_basis": "근거"}],
            "cca_f_tag": "n/a",
        },
        status="passed", drop_reason=None, regen_count=0, fetched_at="2026-11-05",
    )


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    path = tmp_path / "quiz.db"
    monkeypatch.setenv("QUIZ_DB", str(path))
    conn = db.connect(path)
    apply_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture
def pooled_db(tmp_db):
    make_question(tmp_db, "b20261105-99-001")
    freeze(tmp_db)
    tmp_db.commit()
    return tmp_db


def loads(text):
    return json.loads(text)
