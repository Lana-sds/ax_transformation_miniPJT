"""교차 풀이 점검(T2.10). Claude 계열이 아닌 모델이 정답 키를 보지 않고 passed 문제를 푼다. 모델은 가짜다."""

import json

import pytest

from llm_fakes import FakeModel
from quiz import crosscheck, store
from quiz.pool import freeze

PAGE = "/oss/python/langgraph/graph-api"
NOVA, OSS = crosscheck.MODELS

SECRET = {
    "answer_key": ["SECRET_KEY_X"],
    "accepted_answers": ["SECRET_ACCEPTED"],
    "explanation_ko": "SECRET_EXPLANATION 해설",
    "segment": "SECRET_SEGMENT_KO",
    "quote": "SECRET_QUOTE_" + "q" * 30,
    "answer_basis": "SECRET_BASIS",
}


def question(fmt="single", answer_key=("B",)) -> dict:
    q = {
        "question_id": "b20261105-01-001", "format": fmt, "stem_en": "Which edge runs?",
        "choices": [{"id": c, "text": f"choice {c}"} for c in "ABCD"] if fmt != "short" else None,
        "select_count": 2 if fmt == "multi" else None,
        "answer_key": list(answer_key),
        "accepted_answers": ["add_node", SECRET["accepted_answers"][0]] if fmt == "short" else None,
        "explanation_ko": SECRET["explanation_ko"],
        "segments": [{"segment_id": "s1", "en": "Which edge runs?", "ko": SECRET["segment"]}],
        "grounding_records": [{"page": PAGE, "quote": SECRET["quote"], "answer_basis": SECRET["answer_basis"]}],
        "pages": [PAGE],
    }
    return q


def snaps():
    return {PAGE: "DOCUMENT TEXT"}


# --- (1) 프롬프트에 정답 정보가 없다 ---

@pytest.mark.parametrize("fmt", ["single", "multi", "short"])
def test_prompt_hides_answer_and_grounding(fmt):
    q = question(fmt, answer_key=("SECRET_KEY_X",))
    prompt = crosscheck.build_prompt(q, snaps())
    for value in SECRET.values():
        if isinstance(value, list):
            value = value[0]
        assert value not in prompt
    assert "Which edge runs?" in prompt
    assert "DOCUMENT TEXT" in prompt


def test_prompt_has_choices_and_select_count():
    prompt = crosscheck.build_prompt(question("multi"), snaps())
    assert "choice C" in prompt
    assert "Select 2" in prompt


# --- (2) 판정 ---

def ans(answer, unanswerable=False, sentence="Static edges still run."):
    return {"unanswerable": unanswerable, "answer": ", ".join(answer), "supporting_sentence": sentence}


def test_verdict_match_mismatch_unanswerable():
    q = question("single")
    assert crosscheck.verdict(q, ans(["B"])) == "match"
    assert crosscheck.verdict(q, ans(["C"])) == "mismatch"
    assert crosscheck.verdict(q, ans([], unanswerable=True)) == "unanswerable"


def test_empty_answer_without_unanswerable_is_error():
    assert crosscheck.verdict(question("single"), ans([])) == "error"


def test_verdict_normalizes_choice_label():
    assert crosscheck.verdict(question("single"), ans(["b) choice B"])) == "match"


def test_verdict_multi_and_short():
    assert crosscheck.verdict(question("multi", ("A", "C")), ans(["C", "A"])) == "match"
    assert crosscheck.verdict(question("multi", ("A", "C")), ans(["A"])) == "mismatch"
    assert crosscheck.verdict(question("short", ("add_node",)), ans(["add_node()"])) == "match"
    assert crosscheck.verdict(question("short", ("add_node",)), ans(["compile"])) == "mismatch"


@pytest.mark.parametrize("verdicts,priority,flagged,weak", [
    (("match", "match"), None, False, False),
    (("mismatch", "mismatch"), 1, True, False),
    (("mismatch", "match"), 2, True, False),
    (("match", "unanswerable"), None, True, False),
    (("unanswerable", "unanswerable"), None, True, True),
    (("mismatch", "unanswerable"), 2, True, False),
])
def test_item_flags(verdicts, priority, flagged, weak):
    flags = crosscheck.flags(dict(zip(crosscheck.MODELS, verdicts)))
    assert flags == {"priority": priority, "flagged": flagged, "weak_grounding": weak}


def test_check_question_runs_both_models():
    models = {NOVA: FakeModel(ans(["B"])), OSS: FakeModel(ans(["D"]))}
    item = crosscheck.check_question(question("single"), snaps(), models)
    assert item["results"][NOVA]["verdict"] == "match"
    assert item["results"][OSS]["verdict"] == "mismatch"
    assert item["results"][OSS]["supporting_sentence"] == "Static edges still run."
    assert item["priority"] == 2 and item["reviewed"] is None
    for m in models.values():
        assert "SECRET_EXPLANATION" not in m.prompts[0]


def test_model_error_recorded_not_raised():
    class Boom(FakeModel):
        def with_structured_output(self, schema, include_raw=False):
            raise RuntimeError("throttled")
    item = crosscheck.check_question(question("single"), snaps(), {NOVA: Boom(None), OSS: FakeModel(ans(["B"]))})
    assert item["results"][NOVA]["verdict"] == "error"
    assert "throttled" in item["results"][NOVA]["error"]


# --- (3) 리전 ---

@pytest.mark.parametrize("region", ["us-west-2", "ap-northeast-2"])
def test_wrong_region_errors(monkeypatch, region):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.setenv("AWS_DEFAULT_REGION", region)
    with pytest.raises(crosscheck.CrosscheckRegionError):
        crosscheck.check_region()


def test_us_east_1_ok(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    crosscheck.check_region()


# --- 대상, 파일 ---

def seed_questions(conn):
    from conftest import make_question
    make_question(conn, "b20261105-99-001")
    make_question(conn, "b20261105-99-002", fmt="code")
    conn.execute("UPDATE grounding_records SET page = ?", (PAGE,))
    conn.commit()


def test_targets_by_batch_skip_code(tmp_db):
    seed_questions(tmp_db)
    qs = crosscheck.load_targets(tmp_db, batch_id="b20261105-99")
    assert [q["question_id"] for q in qs] == ["b20261105-99-001"]
    assert qs[0]["pages"] == [PAGE]
    qs = crosscheck.load_targets(tmp_db, batch_id="b20261105-99", include_code=True)
    assert len(qs) == 2


def test_targets_by_pool(tmp_db):
    seed_questions(tmp_db)
    psid, _ = freeze(tmp_db)
    qs = crosscheck.load_targets(tmp_db, pool_id=psid)
    assert [q["question_id"] for q in qs] == ["b20261105-99-001"]


def test_run_writes_file_and_keeps_reviews(tmp_db, tmp_path, monkeypatch):
    seed_questions(tmp_db)
    monkeypatch.setattr(crosscheck, "OUT_DIR", tmp_path)
    monkeypatch.setattr(crosscheck, "read_snapshots", lambda pages: {p: "DOC" for p in pages})
    models = {NOVA: FakeModel(ans(["B"])), OSS: FakeModel(ans(["A"]))}
    path = crosscheck.run(batch_id="b20261105-99", models=models)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "b20261105-99.json"
    item = data["items"][0]
    assert set(item["results"]) == {NOVA, OSS}
    assert item["priority"] == 2
    assert data["summary"]["flagged"] == ["b20261105-99-001"]
    assert (tmp_path / "b20261105-99.md").exists()
    # 사용자 검토 값은 다시 돌려도 남는다
    item["reviewed"] = "ok"
    path.write_text(json.dumps(data), encoding="utf-8")
    crosscheck.run(batch_id="b20261105-99", models=models)
    again = json.loads(path.read_text(encoding="utf-8"))
    assert again["items"][0]["reviewed"] == "ok"


def test_run_does_not_touch_db(tmp_db, tmp_path, monkeypatch):
    seed_questions(tmp_db)
    monkeypatch.setattr(crosscheck, "OUT_DIR", tmp_path)
    monkeypatch.setattr(crosscheck, "read_snapshots", lambda pages: {p: "DOC" for p in pages})
    before = tmp_db.execute("SELECT question_id, status, updated_at FROM questions ORDER BY 1").fetchall()
    crosscheck.run(batch_id="b20261105-99", models={NOVA: FakeModel(ans(["C"])), OSS: FakeModel(ans(["C"]))})
    after = tmp_db.execute("SELECT question_id, status, updated_at FROM questions ORDER BY 1").fetchall()
    assert [tuple(r) for r in before] == [tuple(r) for r in after]
    assert store  # store는 읽기용으로만 쓴다


def test_cli_arguments():
    from quiz.cli import build_parser
    p = build_parser()
    a = p.parse_args(["crosscheck", "--batch", "b20261105-02"])
    assert (a.batch, a.pool, a.include_code) == ("b20261105-02", None, False)
    a = p.parse_args(["crosscheck", "--pool", "p1", "--include-code"])
    assert (a.pool, a.include_code) == ("p1", True)
    with pytest.raises(SystemExit):
        p.parse_args(["crosscheck"])
