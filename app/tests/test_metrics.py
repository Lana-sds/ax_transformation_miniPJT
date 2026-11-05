"""T6.1 기준선 지표(design.md 5.4, requirements 7.3)."""

import json

from quiz import metrics, store
from quiz.cli import main
from quiz.pool import current_pool
from quiz_helpers import add_attempt, add_set, make_pool

KEYS = {"generated_at", "pool_snapshot_id", "judge_pass_rate", "drops", "sets", "batches"}


def _verify(conn, qid, attempt_no, judge_pass):
    conn.execute(
        "INSERT INTO verification_results (question_id, attempt_no, judge_pass, created_at) VALUES (?, ?, ?, ?)",
        (qid, attempt_no, judge_pass, "2026-11-05T00:00:00Z"),
    )


def _drop(conn, qid, reason):
    conn.execute("UPDATE questions SET status = 'dropped', drop_reason = ? WHERE question_id = ?", (reason, qid))


def test_build_matches_db(tmp_db):
    ids = make_pool(tmp_db, 12)
    psid = current_pool(tmp_db)
    _verify(tmp_db, ids[0], 0, 0)
    _verify(tmp_db, ids[0], 1, 1)
    _verify(tmp_db, ids[1], 0, 1)
    _verify(tmp_db, ids[2], 0, None)  # Judge 전에 끝난 시도는 세지 않는다
    tmp_db.execute(
        "UPDATE batches SET started_at = '2026-11-05T00:00:00Z', finished_at = '2026-11-05T00:01:30Z',"
        " input_tokens = 100, output_tokens = 20, cost_usd = 0.5"
    )
    store.insert_batch(tmp_db, "b20261105-97", "pool", "gen", "judge")  # 끝나지 않은 배치
    set_id = add_set(tmp_db, 1, ids[:10])
    for i, q in enumerate(ids[:10]):
        add_attempt(tmp_db, set_id, q, correct=i < 7)
    # 풀 고정 뒤 버린 문제: 풀 스냅샷과 무관하게 questions에서 센다
    _drop(tmp_db, ids[10], "duplicate")
    _drop(tmp_db, ids[11], "regen_exhausted")
    tmp_db.commit()

    m = metrics.build(tmp_db)

    assert set(m) == KEYS
    assert m["pool_snapshot_id"] == psid
    assert m["judge_pass_rate"] == {"attempts": 3, "passed": 2, "rate": round(2 / 3, 4)}
    assert m["drops"] == {"total": 2, "by_reason": {"duplicate": 1, "regen_exhausted": 1}}
    assert m["sets"] == [{"set_no": 1, "set_id": set_id, "correct": 7, "total": 10, "rate": 0.7}]
    b = {x["batch_id"]: x for x in m["batches"]}
    assert b["b20261105-99"] == {"batch_id": "b20261105-99", "kind": "pool", "input_tokens": 100,
                                 "output_tokens": 20, "cost_usd": 0.5, "seconds": 90}
    assert b["b20261105-97"]["seconds"] is None
    assert b["b20261105-97"]["cost_usd"] is None


def test_sets_only_current_pool(tmp_db):
    old = make_pool(tmp_db, 2)
    old_set = add_set(tmp_db, 1, old)
    add_attempt(tmp_db, old_set, old[0], correct=True)
    ids = make_pool(tmp_db, 3)  # 문제 집합이 바뀌면 새 풀 스냅샷이다
    new_set = add_set(tmp_db, 2, ids)
    m = metrics.build(tmp_db)
    assert [s["set_id"] for s in m["sets"]] == [new_set]
    assert m["sets"][0] == {"set_no": 2, "set_id": new_set, "correct": 0, "total": 3, "rate": 0.0}


def test_empty_db(tmp_db):
    m = metrics.build(tmp_db)
    assert m["pool_snapshot_id"] is None
    assert m["judge_pass_rate"] == {"attempts": 0, "passed": 0, "rate": 0.0}
    assert m["drops"] == {"total": 0, "by_reason": {}}
    assert m["sets"] == [] and m["batches"] == []


def test_cli_writes_file(tmp_db, tmp_path, monkeypatch, capsys):
    make_pool(tmp_db, 1)
    out = tmp_path / "metrics" / "baseline.json"
    monkeypatch.setattr(metrics, "BASELINE_PATH", out)
    assert main(["metrics"]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == KEYS
    assert f"file={out}" in capsys.readouterr().out
