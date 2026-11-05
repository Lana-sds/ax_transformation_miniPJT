"""T5.2 감사 표본과 결과(design.md 6.6, requirements 7.2)."""

import hashlib
import random

import pytest
from fastapi.testclient import TestClient

from quiz import audit
from quiz.pool import current_pool
from quiz.server import app
from quiz_helpers import make_pool

OK = {"answer_key_error": False, "quote_unsupported": False, "mapping_unfaithful": False}


@pytest.fixture
def pool_db(tmp_db):
    make_pool(tmp_db, 30)
    return tmp_db


def test_seed_and_sample_follow_design(pool_db):
    psid = current_pool(pool_db)
    a = audit.create(pool_db)
    seed = int(hashlib.sha256(psid.encode("utf-8")).hexdigest()[:16], 16)
    ids = [r[0] for r in pool_db.execute(
        "SELECT question_id FROM pool_snapshot_items WHERE pool_snapshot_id = ?", (psid,))]
    assert a["pool_snapshot_id"] == psid
    assert a["seed"] == str(seed)
    assert a["sample"] == random.Random(seed).sample(sorted(ids), 20)


def test_same_snapshot_returns_existing_audit(pool_db):
    first = audit.create(pool_db)
    second = audit.create(pool_db)
    assert second["audit_id"] == first["audit_id"]
    assert second["sample"] == first["sample"]
    assert pool_db.execute("SELECT COUNT(*) FROM audits").fetchone()[0] == 1


def test_pool_smaller_than_sample_is_rejected(tmp_db):
    make_pool(tmp_db, 19)
    with pytest.raises(audit.PoolTooSmall):
        audit.create(tmp_db)


def test_no_pool_is_rejected(tmp_db):
    with pytest.raises(audit.NoPool):
        audit.create(tmp_db)


def _record_all(conn, a, errors: dict[str, int]):
    """앞에서부터 판정별로 errors[k]개 문항을 True로 둔다."""
    for i, qid in enumerate(a["sample"]):
        flags = {k: i < errors.get(k, 0) for k in OK}
        audit.record(conn, a["audit_id"], qid, **flags)


@pytest.mark.parametrize("errors, expected", [
    ({}, "pass"),
    ({"answer_key_error": 1}, "pass"),
    ({"answer_key_error": 2}, "fail"),
    ({"quote_unsupported": 2}, "pass"),
    ({"quote_unsupported": 3}, "fail"),
    ({"mapping_unfaithful": 2}, "pass"),
    ({"mapping_unfaithful": 3}, "fail"),
    ({"answer_key_error": 1, "quote_unsupported": 2, "mapping_unfaithful": 2}, "pass"),
])
def test_result_thresholds(pool_db, errors, expected):
    a = audit.create(pool_db)
    _record_all(pool_db, a, errors)
    assert audit.get(pool_db, a["audit_id"])["result"] == expected


def test_result_waits_for_all_twenty(pool_db):
    a = audit.create(pool_db)
    for qid in a["sample"][:19]:
        audit.record(pool_db, a["audit_id"], qid, **OK)
    assert audit.get(pool_db, a["audit_id"])["result"] is None
    audit.record(pool_db, a["audit_id"], a["sample"][19], **OK)
    assert audit.get(pool_db, a["audit_id"])["result"] == "pass"


def test_rerecord_updates_row_and_result(pool_db):
    a = audit.create(pool_db)
    _record_all(pool_db, a, {"answer_key_error": 2})
    assert audit.get(pool_db, a["audit_id"])["result"] == "fail"
    audit.record(pool_db, a["audit_id"], a["sample"][1], **OK, note="다시 보니 맞다")
    got = audit.get(pool_db, a["audit_id"])
    assert got["result"] == "pass"
    assert pool_db.execute("SELECT COUNT(*) FROM audit_records").fetchone()[0] == 20
    assert got["records"][a["sample"][1]]["note"] == "다시 보니 맞다"


def test_record_outside_sample_is_rejected(pool_db):
    a = audit.create(pool_db)
    outside = next(q for q in (f"b20261105-99-{i:03d}" for i in range(1, 31)) if q not in a["sample"])
    with pytest.raises(audit.NotInSample):
        audit.record(pool_db, a["audit_id"], outside, **OK)


def test_api_flow(pool_db):
    with TestClient(app) as client:
        assert client.get("/api/audits/current").status_code == 404
        a = client.post("/api/audits").json()
        assert len(a["questions"]) == 20
        q = a["questions"][0]
        assert q["answer_key"] == ["B"] and q["segments"] and q["grounding"][0]["quote"]
        assert client.post("/api/audits").json()["audit_id"] == a["audit_id"]
        r = client.put(f"/api/audits/{a['audit_id']}/records/{q['question_id']}",
                       json={**OK, "answer_key_error": True, "note": "키 틀림"})
        assert r.status_code == 200
        cur = client.get("/api/audits/current").json()
        assert cur["audit_id"] == a["audit_id"]
        assert cur["records"][q["question_id"]]["answer_key_error"] is True
        assert cur["result"] is None
        bad = client.put(f"/api/audits/{a['audit_id']}/records/nope", json=OK)
        assert bad.status_code == 400
        assert client.put(f"/api/audits/missing/records/{q['question_id']}", json=OK).status_code == 404


def test_api_pool_too_small(tmp_db):
    make_pool(tmp_db, 5)
    with TestClient(app) as client:
        r = client.post("/api/audits")
        assert r.status_code == 409
        assert r.json()["detail"]["reason"] == "pool_too_small"
