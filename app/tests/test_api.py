import pytest
from fastapi.testclient import TestClient

from quiz.pool import freeze
from quiz.server import app
from quiz_helpers import make_pool, make_short, review_row

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


def _answer(client, set_id, question_id, answer):
    return client.post(f"/api/sets/{set_id}/answers", json={"question_id": question_id, "answer": answer})


def _tag(client, attempt_id, tag, segment=None):
    body = {"mistake_tag": tag}
    if segment is not None:
        body["confused_segment_id"] = segment
    return client.put(f"/api/attempts/{attempt_id}/tag", json=body)


def test_short_answer_matches_accepted_answers(tmp_db):
    make_pool(tmp_db, 9)
    short = make_short(tmp_db, 10)
    freeze(tmp_db)
    tmp_db.commit()
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        assert short in [q["question_id"] for q in s["questions"]]
        body = _answer(client, s["set_id"], short, "  StateGraph.ADD_NODE ").json()
        assert body["correct"] is True
        assert body["answer_key"] == ["add_node"]


def test_short_answer_wrong_is_incorrect(tmp_db):
    make_pool(tmp_db, 9)
    short = make_short(tmp_db, 10)
    freeze(tmp_db)
    tmp_db.commit()
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        assert _answer(client, s["set_id"], short, "add_edge").json()["correct"] is False


def test_untagged_wrong_blocks_next_question_with_409(pool_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        q1, q2 = (q["question_id"] for q in s["questions"][:2])
        wrong = _answer(client, s["set_id"], q1, "A").json()
        r = _answer(client, s["set_id"], q2, "B")
        assert r.status_code == 409
        assert r.json()["detail"]["reason"] == "untagged_wrong"
        assert r.json()["detail"]["attempt_ids"] == [wrong["attempt_id"]]
        assert _tag(client, wrong["attempt_id"], "concept").status_code == 200
        assert _answer(client, s["set_id"], q2, "B").status_code == 200
    assert pool_db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 2


def test_untagged_wrong_blocks_next_set_with_409(pool_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        wrong = _answer(client, s["set_id"], s["questions"][0]["question_id"], "A").json()
        r = client.post("/api/sets")
        assert r.status_code == 409
        assert r.json()["detail"]["reason"] == "untagged_wrong"
        assert pool_db.execute("SELECT COUNT(*) FROM quiz_sets").fetchone()[0] == 1
        assert _tag(client, wrong["attempt_id"], "reading", "s1").status_code == 200
        assert client.post("/api/sets").status_code == 200


def test_tag_only_on_wrong_rows_and_validates_reading_segment(pool_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        right = _answer(client, s["set_id"], s["questions"][0]["question_id"], "B").json()
        assert _tag(client, right["attempt_id"], "concept").status_code == 409
        wrong = _answer(client, s["set_id"], s["questions"][1]["question_id"], "A").json()
        assert _tag(client, wrong["attempt_id"], "reading").status_code == 422          # 구절 없음
        assert _tag(client, wrong["attempt_id"], "reading", "s9").status_code == 422    # 없는 구절
        assert _tag(client, wrong["attempt_id"], "careless").status_code == 422
        assert _tag(client, 9999, "concept").status_code == 404
        r = _tag(client, wrong["attempt_id"], "reading", "s1")
        assert r.status_code == 200
        assert r.json()["mistake_tag"] == "reading" and r.json()["confused_segment_id"] == "s1"
        assert r.json()["review"] == {"review_round": 1, "due_set_no": 3, "state": "pending", "mistake_tag": "reading"}
    row = pool_db.execute("SELECT mistake_tag, confused_segment_id FROM attempts WHERE attempt_id = ?",
                          (right["attempt_id"],)).fetchone()
    assert tuple(row) == (None, None)


def test_retag_changes_tag_without_moving_review(pool_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        q = s["questions"][0]["question_id"]
        wrong = _answer(client, s["set_id"], q, "A").json()
        _tag(client, wrong["attempt_id"], "reading", "s1")
        r = _tag(client, wrong["attempt_id"], "concept")
        assert r.status_code == 200
        assert r.json()["confused_segment_id"] is None
        assert r.json()["review"] == {"review_round": 1, "due_set_no": 3, "state": "pending", "mistake_tag": "concept"}
        # 다음 세트가 생긴 뒤에는 앞 세트의 태그를 바꾸지 않는다
        client.post("/api/sets")
        assert _tag(client, wrong["attempt_id"], "reading", "s1").status_code == 409


def test_answer_to_older_set_is_refused(pool_db):
    """복습 간격은 세트 번호로 센다. 새 세트가 생긴 뒤 앞 세트에 답하면 간격이 꼬이므로 막는다."""
    with TestClient(app) as client:
        s1 = client.post("/api/sets").json()
        client.post("/api/sets")
        r = _answer(client, s1["set_id"], s1["questions"][0]["question_id"], "B")
        assert r.status_code == 409
        assert r.json()["detail"]["reason"] == "set_closed"


def test_get_set_resumes_with_answered_results(pool_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        q1, q2 = (q["question_id"] for q in s["questions"][:2])
        _answer(client, s["set_id"], q1, "B")
        wrong = _answer(client, s["set_id"], q2, "A").json()
        r = client.get(f"/api/sets/{s['set_id']}")
        assert r.status_code == 200
        body = r.json()
        assert body["set_id"] == s["set_id"] and body["set_no"] == 1
        assert [q["question_id"] for q in body["questions"]] == [q["question_id"] for q in s["questions"]]
        assert not any(HIDDEN & set(q) for q in body["questions"])
        assert set(body["results"]) == {q1, q2}
        assert body["results"][q1]["correct"] is True and body["results"][q1]["answer_key"] == ["B"]
        assert body["results"][q2]["mistake_tag"] is None
        assert body["untagged_attempt_ids"] == [wrong["attempt_id"]]
        assert body["completed"] is False
        assert client.get("/api/sets/nope").status_code == 404


def test_set_completed_after_all_answers(pool_db):
    with TestClient(app) as client:
        s = client.post("/api/sets").json()
        for q in s["questions"]:
            _answer(client, s["set_id"], q["question_id"], "B")
        assert client.get(f"/api/sets/{s['set_id']}").json()["completed"] is True
    assert pool_db.execute("SELECT completed_at FROM quiz_sets").fetchone()[0] is not None


def test_review_flow_through_api(pool_db):
    """1번 세트 오답 → 3번 세트에 복습으로 나오고, 맞히면 cleared."""
    with TestClient(app) as client:
        s1 = client.post("/api/sets").json()
        q = s1["questions"][0]["question_id"]
        wrong = _answer(client, s1["set_id"], q, "A").json()
        _tag(client, wrong["attempt_id"], "concept")
        client.post("/api/sets")  # 2번 세트: 기한 전
        s3 = client.post("/api/sets").json()
        assert s3["questions"][0]["question_id"] == q
        assert _answer(client, s3["set_id"], q, "B").json()["correct"] is True
    assert review_row(pool_db, q)["state"] == "cleared"
