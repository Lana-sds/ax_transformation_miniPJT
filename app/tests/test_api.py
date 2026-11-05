import pytest
from fastapi.testclient import TestClient

from quiz.server import app
from quiz_helpers import make_pool

HIDDEN = {"answer_key", "explanation_ko", "segments", "grounding", "answer_key_json"}


@pytest.fixture
def pool_db(tmp_db):
    make_pool(tmp_db, 12)
    return tmp_db


def test_set_hides_answer_and_answer_reveals_result(pool_db):
    with TestClient(app) as client:
        assert client.get("/api/health").json()["pool_snapshot_id"].startswith("ps_")
        s = client.post("/api/sets").json()
        assert len(s["questions"]) == 10
        q = s["questions"][0]
        assert not HIDDEN & set(q)
        r = client.post(f"/api/sets/{s['set_id']}/answers", json={"question_id": q["question_id"], "answer": "B"})
        assert r.status_code == 200
        body = r.json()
        assert body["correct"] is True
        assert body["answer_key"] == ["B"]
        assert body["explanation_ko"] and body["segments"]
        assert body["grounding"][0]["url"] == "https://docs.langchain.com/oss/python/langgraph/graph-api"
        again = client.post(f"/api/sets/{s['set_id']}/answers", json={"question_id": q["question_id"], "answer": "A"})
        assert again.status_code == 409
    assert pool_db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1


def test_wrong_answer_is_graded_incorrect(pool_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        q = s["questions"][0]
        body = client.post(f"/api/sets/{s['set_id']}/answers", json={"question_id": q["question_id"], "answer": ["C"]}).json()
        assert body["correct"] is False


def test_set_refused_when_pool_has_fewer_than_ten(pooled_db):
    with TestClient(app) as client:
        r = client.post("/api/sets")
        assert r.status_code == 409
    assert pooled_db.execute("SELECT COUNT(*) FROM quiz_sets").fetchone()[0] == 0
