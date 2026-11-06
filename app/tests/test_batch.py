"""배치 CLI(T2.7, design.md 6.2, 7.2). 모델과 게이트는 가짜로 바꾼다. 허용 목록과 스냅샷은 저장소 것을 쓴다."""

import threading
import time

import pytest

from llm_fakes import FakeModel
from quiz import allowlist, batch, slots, store
from conftest import make_question
from quiz.cli import build_parser
from test_generate import payload
from test_judge import PASS


class PayloadByFormat(FakeModel):
    """생성 스키마 이름으로 형식을 알아 그 형식 payload를 준다. fail_from번째 호출부터 예외를 던진다."""

    def __init__(self, fail_from: int | None = None, same: bool = False):
        super().__init__(None)
        self.fail_from = fail_from
        self.same = same  # True면 모든 슬롯에 같은 본문과 같은 인용을 준다(dedupe 경합 재현)
        self.lock = threading.Lock()

    def with_structured_output(self, schema, include_raw=False):
        parent = self

        class S:
            def invoke(self, prompt):
                with parent.lock:
                    parent.prompts.append(prompt)
                    n = len(parent.prompts)
                if parent.fail_from is not None and n >= parent.fail_from:
                    raise RuntimeError("interrupted")
                fmt = {"SingleQuestion": "single", "MultiQuestion": "multi", "ShortQuestion": "short",
                       "CodeQuestion": "code"}[schema.__name__]
                p = payload(fmt)
                # 슬롯마다 본문과 인용이 달라야 dedupe에 걸리지 않는다
                k = 0 if parent.same else n
                p["stem_en"] = f"Question number {k} about {fmt} " + "x" * k
                p["grounding_records"] = [{**p["grounding_records"][0], "quote": f"quote {k} " + "q" * 40}]
                from langchain_core.messages import AIMessage
                raw = AIMessage(content="", usage_metadata={"input_tokens": 100, "output_tokens": 20,
                                                            "total_tokens": 120})
                return {"raw": raw, "parsed": schema.model_validate(p), "parsing_error": None}
        return S()


def code_ok_predictions():
    return [{"choice_id": c["choice_id"], **c["expected"]} for c in payload("code")["exec_spec"]]


def models(fail_from=None):
    judge = FakeModel(PASS | {"exec_predictions": code_ok_predictions()})
    run = {c["code"]: c["expected"] for c in payload("code")["exec_spec"]}
    return dict(gen_model=PayloadByFormat(fail_from), judge_model=judge,
                gate_fn=lambda *a, **k: [], run=lambda code: run[code])


def statuses(conn, batch_id):
    return dict(conn.execute("SELECT question_id, status FROM questions WHERE batch_id = ?", (batch_id,)).fetchall())


@pytest.fixture(autouse=True)
def no_backup(monkeypatch):
    monkeypatch.setattr(batch, "backup", lambda *a, **k: None)


def test_pilot_plans_one_slot_per_bucket(tmp_db):
    m = models()
    batch_id = batch.run_batch(plan="pilot", **m)
    rows = tmp_db.execute("SELECT bucket, format FROM batch_slots WHERE batch_id = ? ORDER BY slot_no",
                          (batch_id,)).fetchall()
    assert [r[0] for r in rows] == slots.BUCKETS
    assert {r[1] for r in rows} == set(slots.FORMATS)
    assert set(statuses(tmp_db, batch_id).values()) == {"passed"}
    assert tmp_db.execute("SELECT finished_at FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()[0]


def test_pool_count_limits_slots(tmp_db):
    batch_id = batch.run_batch(plan="pool", count=3, **models())
    assert tmp_db.execute("SELECT COUNT(*) FROM batch_slots WHERE batch_id = ?", (batch_id,)).fetchone()[0] == 3


def test_pool_plan_has_sixty_slots():
    rows = allowlist.load_rows()
    assert len(batch.make_plan(rows, "pool")) == 60


def test_interrupted_batch_resumes_only_unfinished_slots(tmp_db):
    # 처음 2슬롯만 끝나고 그 뒤 호출은 모두 실패한다(중단)
    first = models(fail_from=3)
    batch_id = batch.run_batch(plan="pilot", workers=1, **first)
    done = statuses(tmp_db, batch_id)
    assert len(done) == 2
    assert tmp_db.execute("SELECT finished_at FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()[0] is None
    before = dict(tmp_db.execute("SELECT question_id, updated_at FROM questions").fetchall())

    second = models()
    assert batch.run_batch(resume=batch_id, **second) == batch_id
    after = statuses(tmp_db, batch_id)
    assert len(after) == 6 and set(after.values()) == {"passed"}
    assert len(second["gen_model"].prompts) == 4  # 끝난 2슬롯은 다시 돌지 않았다
    for qid, ts in before.items():
        assert tmp_db.execute("SELECT updated_at FROM questions WHERE question_id = ?", (qid,)).fetchone()[0] == ts


def test_resume_rebuilds_slot_pages_from_allowlist(tmp_db):
    rows = allowlist.load_rows()
    planned = batch.make_plan(rows, "pilot")
    for s in planned:
        rebuilt = slots.slot_for(rows, s["bucket"], s["topic"], s["format"], s["question_type"])
        assert rebuilt["pages"] == s["pages"] and rebuilt["near"] == s["near"]


def test_two_workers_finish_all_slots(tmp_db):
    batch_id = batch.run_batch(plan="pilot", workers=2, **models())
    assert len(statuses(tmp_db, batch_id)) == 6


def test_cli_generate_arguments():
    p = build_parser()
    a = p.parse_args(["generate", "--plan", "pilot"])
    assert (a.plan, a.count, a.resume) == ("pilot", None, None)
    a = p.parse_args(["generate", "--plan", "pool", "--count", "5"])
    assert (a.plan, a.count) == ("pool", 5)
    a = p.parse_args(["generate", "--resume", "b20261105-02"])
    assert a.resume == "b20261105-02"
    with pytest.raises(SystemExit):
        p.parse_args(["generate"])
    with pytest.raises(SystemExit):
        p.parse_args(["generate", "--plan", "pilot", "--resume", "b20261105-02"])


def test_fill_plan_counts_existing_passed():
    rows = allowlist.load_rows()
    have = [{"bucket": "rag", "topic": "x", "format": "single"}] * 10
    plan = batch.make_plan(rows, "fill", have=have)
    assert len(plan) == 50
    assert all(s["bucket"] != "rag" for s in plan)


def test_fill_batch_reads_passed_questions_from_db(tmp_db, monkeypatch):
    seen = {}
    real = batch.make_plan

    def spy(rows, kind, count=None, have=None, tried=None):
        seen["kind"], seen["have"] = kind, have
        return real(rows, kind, count, have, tried)

    monkeypatch.setattr(batch, "make_plan", spy)
    make_question(tmp_db, "b20261105-99-001")
    tmp_db.commit()
    batch_id = batch.run_batch(plan="fill", count=2, **models())
    assert seen["kind"] == "fill"
    assert seen["have"] == [{"bucket": "langgraph_basics", "topic": "t", "format": "single"}]
    assert tmp_db.execute("SELECT COUNT(*) FROM batch_slots WHERE batch_id = ?", (batch_id,)).fetchone()[0] == 2


def test_cli_generate_accepts_fill():
    a = build_parser().parse_args(["generate", "--plan", "fill"])
    assert a.plan == "fill"


def test_fill_batch_passes_dropped_questions_as_tried(tmp_db, monkeypatch):
    seen = {}
    real = batch.make_plan

    def spy(rows, kind, count=None, have=None, tried=None):
        seen["tried"] = tried
        return real(rows, kind, count, have, tried)

    monkeypatch.setattr(batch, "make_plan", spy)
    make_question(tmp_db, "b20261105-99-001")
    tmp_db.execute("UPDATE questions SET status = 'dropped', drop_reason = 'duplicate'")
    tmp_db.commit()
    batch.run_batch(plan="fill", count=1, **models())
    assert seen["tried"] == [{"bucket": "langgraph_basics", "topic": "t", "format": "single"}]


def test_resume_keeps_audit_failed_question(tmp_db):
    """감사에서 빠진 문제(audit_failed)는 끝난 슬롯이다. 재개가 다시 만들거나 덮어쓰지 않는다(F-3)."""
    first = models(fail_from=3)
    batch_id = batch.run_batch(plan="pilot", workers=1, **first)
    failed = store.question_id(batch_id, 1)
    tmp_db.execute("UPDATE questions SET status = 'audit_failed' WHERE question_id = ?", (failed,))
    tmp_db.commit()
    before = tuple(tmp_db.execute("SELECT stem_en, updated_at FROM questions WHERE question_id = ?",
                                  (failed,)).fetchone())

    second = models()
    batch.run_batch(resume=batch_id, **second)
    assert len(second["gen_model"].prompts) == 4  # 끝나지 않은 4슬롯만 돈다
    row = tmp_db.execute("SELECT status, stem_en, updated_at FROM questions WHERE question_id = ?",
                         (failed,)).fetchone()
    assert tuple(row) == ("audit_failed", *before)
    assert batch.unfinished(batch_id) == 0
    assert tmp_db.execute("SELECT finished_at FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()[0]

    third = models()
    batch.run_batch(resume=batch_id, **third)
    assert third["gen_model"].prompts == []
    assert tmp_db.execute("SELECT status FROM questions WHERE question_id = ?", (failed,)).fetchone()[0] \
        == "audit_failed"


class SlowJudge(FakeModel):
    """Judge 호출마다 잠깐 멈춘다. 두 슬롯이 동시에 dedupe에 닿게 한다."""

    def with_structured_output(self, schema, include_raw=False):
        inner = super().with_structured_output(schema, include_raw)

        class S:
            def invoke(self, prompt):
                time.sleep(0.5)
                return inner.invoke(prompt)
        return S()


def test_parallel_slots_in_same_bucket_dedupe_each_other(tmp_db):
    """같은 버킷 두 슬롯이 동시에 같은 문제를 만들면 하나만 passed, 하나는 duplicate로 버린다(F-5)."""
    m = models()
    m["gen_model"] = PayloadByFormat(same=True)
    m["judge_model"] = SlowJudge(PASS | {"exec_predictions": code_ok_predictions()})
    batch_id = batch.run_batch(plan="pool", count=2, workers=2, **m)
    buckets = {r[0] for r in tmp_db.execute("SELECT bucket FROM batch_slots WHERE batch_id = ?", (batch_id,))}
    assert len(buckets) == 1
    rows = tmp_db.execute("SELECT question_id, status, drop_reason FROM questions WHERE batch_id = ?"
                          " ORDER BY question_id", (batch_id,)).fetchall()
    assert sorted((r[1], r[2] or "") for r in rows) == [("dropped", "duplicate"), ("passed", "")]
    passed = next(r[0] for r in rows if r[1] == "passed")
    dropped = next(r[0] for r in rows if r[1] == "dropped")
    v = tmp_db.execute("SELECT duplicate_of, fail_reasons_json FROM verification_results WHERE question_id = ?"
                       " ORDER BY attempt_no DESC LIMIT 1", (dropped,)).fetchone()
    assert v[0] == passed and "duplicate" in v[1]
    assert len(m["gen_model"].prompts) == 2  # duplicate는 재생성하지 않는다
