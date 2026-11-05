from fastapi.testclient import TestClient

from quiz.server import app

HIDDEN = {"answer_key", "explanation_ko", "segments", "grounding", "answer_key_json"}


def test_set_hides_answer_and_answer_reveals_result(pooled_db):
    with TestClient(app) as client:
        assert client.get("/api/health").json()["pool_snapshot_id"].startswith("ps_")
        s = client.post("/api/sets").json()
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
    assert pooled_db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1


def test_wrong_answer_is_graded_incorrect(pooled_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        q = s["questions"][0]
        body = client.post(f"/api/sets/{s['set_id']}/answers", json={"question_id": q["question_id"], "answer": ["C"]}).json()
        assert body["correct"] is False
