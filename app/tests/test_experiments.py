"""04 실험 하네스(1-가). 프롬프트 경로 전환, Judge 항목 설정, 고정 슬롯, `quiz experiment judge|summary`.

모델은 가짜로 바꾼다. Bedrock을 부르지 않는다. 운영 DB 대신 `QUIZ_DB`로 임시 DB를 쓴다.
"""

import hashlib
import json
import shutil
import sqlite3

import pytest

from conftest import make_question
from llm_fakes import FakeModel
from quiz import allowlist, batch, db, experiments
from quiz.cli import build_parser, main
from quiz.pipeline import nodes, prompts, schemas
from test_batch import models as batch_models
from test_generate import payload, state
from test_judge import PASS, judged

QID = "b20261105-99-001"


@pytest.fixture
def prompt_copy(tmp_path, monkeypatch):
    """`packs/langchain/prompts/` 전체 사본. `QUIZ_PROMPTS_DIR`이 이 사본을 가리킨다."""
    d = tmp_path / "prompts"
    shutil.copytree(prompts.DEFAULT_PROMPT_DIR, d)
    monkeypatch.setenv(prompts.ENV, str(d))
    return d


@pytest.fixture
def exp_dir(tmp_path, monkeypatch):
    d = tmp_path / "experiments"
    monkeypatch.setattr(experiments, "EXP_DIR", d)
    return d


@pytest.fixture(autouse=True)
def no_backup(monkeypatch):
    monkeypatch.setattr(batch, "backup", lambda *a, **k: None)


EXTRA = {"extra_items": [{
    "name": "explanation_correct",
    "description": "The Korean explanation is correct per the document",
}]}


def write_extra(d, data=EXTRA):
    (d / nodes.JUDGE_ITEMS_CONFIG).write_text(json.dumps(data), encoding="utf-8")


# --- (1) 프롬프트 경로 ---

def test_prompt_dir_defaults_to_pack(monkeypatch):
    monkeypatch.delenv(prompts.ENV, raising=False)
    assert prompts.prompt_dir() == prompts.DEFAULT_PROMPT_DIR
    assert prompts.DEFAULT_PROMPT_DIR == db.REPO_ROOT / "packs" / "langchain" / "prompts"
    assert not prompts.is_overridden()


def test_prompt_dir_env_switches_judge_prompt(prompt_copy):
    judge_md = prompt_copy / "judge.md"
    judge_md.write_text("VARIANT-JUDGE-MARKER\n" + judge_md.read_text(encoding="utf-8"), encoding="utf-8")
    assert prompts.is_overridden()
    model = FakeModel(PASS)
    nodes.judge(judged("single"), model)
    assert "VARIANT-JUDGE-MARKER" in model.prompts[0]


def test_prompt_dir_env_switches_near_rule_at_call_time(prompt_copy):
    (prompt_copy / "near.md").write_text("VARIANT-NEAR-RULE\n", encoding="utf-8")
    assert nodes.NEAR_RULE == "VARIANT-NEAR-RULE"
    model = FakeModel(payload("single"))
    nodes.generate(state("single", near=True), model)
    assert "VARIANT-NEAR-RULE" in model.prompts[0]


# --- (4) Judge 항목 기본값과 설정 ---

def test_default_judge_items_unchanged(monkeypatch):
    monkeypatch.delenv(prompts.ENV, raising=False)
    assert not (prompts.DEFAULT_PROMPT_DIR / nodes.JUDGE_ITEMS_CONFIG).exists()
    base = ("answer_key_correct", "quote_supports_answer", "distractors_wrong", "mapping_faithful")
    choice = ("distractors_plausible", "no_cue")
    assert nodes.JUDGE_ITEMS == base and nodes.CHOICE_JUDGE_ITEMS == choice
    assert nodes.extra_judge_items() == []
    assert nodes.judge_items("short") == base
    for fmt in ("single", "multi", "code"):
        assert nodes.judge_items(fmt) == base + choice
        assert schemas.verdict_schema(nodes.extra_judge_items(fmt)) is schemas.JudgeVerdict
    model = FakeModel(PASS)
    nodes.judge(judged("single"), model)
    assert model.schemas == [schemas.JudgeVerdict]


def test_judge_items_config_adds_item_to_schema_and_fail_reasons(prompt_copy):
    write_extra(prompt_copy)
    assert nodes.judge_items("single")[-1] == "explanation_correct"
    assert nodes.judge_items("short")[-1] == "explanation_correct"
    model = FakeModel(PASS | {"explanation_correct": False, "verdict": "fail", "reasons": ["wrong explanation"]})
    out = nodes.judge(judged("single"), model)
    assert out["fail_reasons"] == ["judge_fail:explanation_correct"]
    assert out["judge"]["explanation_correct"] is False
    schema = model.schemas[0]
    assert schema.__name__ == "JudgeVerdict"
    js = schema.model_json_schema()
    assert "explanation_correct" in js["required"]
    # 항목은 verdict 앞에 둔다. 모델이 항목을 보고 나서 verdict를 쓰게 한다
    order = list(js["properties"])
    assert order.index("explanation_correct") < order.index("verdict")
    out = nodes.judge(judged("single"), FakeModel(PASS | {"explanation_correct": True}))
    assert out["fail_reasons"] == []


def test_judge_items_config_respects_formats(prompt_copy):
    write_extra(prompt_copy, {"extra_items": [EXTRA["extra_items"][0] | {"formats": ["single"]}]})
    assert "explanation_correct" in nodes.judge_items("single")
    assert "explanation_correct" not in nodes.judge_items("short")
    out = nodes.judge(judged("short"), FakeModel(PASS))
    assert out["fail_reasons"] == []


def test_judge_prompt_lists_extra_items_when_placeholder_present(prompt_copy):
    write_extra(prompt_copy)
    judge_md = prompt_copy / "judge.md"
    judge_md.write_text(judge_md.read_text(encoding="utf-8").replace(
        "{{format_rules}}", "{{extra_items}}\n\n{{format_rules}}"), encoding="utf-8")
    model = FakeModel(PASS | {"explanation_correct": True})
    nodes.judge(judged("single"), model)
    assert "- `explanation_correct`: The Korean explanation is correct per the document" in model.prompts[0]
    assert "{{" not in model.prompts[0]


@pytest.mark.parametrize("bad", [
    {"extra_items": [{"name": "answer_key_correct", "description": "x"}]},
    {"extra_items": [{"name": "verdict", "description": "x"}]},
    {"extra_items": [{"name": "not an id", "description": "x"}]},
    {"extra_items": [{"name": "ok_item"}]},
    {"extra_items": [{"name": "ok_item", "description": "x", "formats": ["essay"]}]},
    {"extra_items": [{"name": "dup", "description": "x"}, {"name": "dup", "description": "y"}]},
])
def test_judge_items_config_rejects_bad_entries(prompt_copy, bad):
    write_extra(prompt_copy, bad)
    with pytest.raises(ValueError):
        nodes.judge_items("single")


# --- 고정 슬롯(--slots) ---

def pilot_slots():
    return batch.make_plan(allowlist.load_rows(), "pilot")


def slot_rows(conn, batch_id):
    return [tuple(r) for r in conn.execute(
        "SELECT bucket, topic, format, question_type FROM batch_slots WHERE batch_id = ? ORDER BY slot_no",
        (batch_id,))]


def test_fixed_slots_are_used_in_given_order(tmp_db, tmp_path):
    chosen = list(reversed(pilot_slots()))[:3]
    path = tmp_path / "slots.json"
    path.write_text(json.dumps({"seed": 7, "slots": chosen}, ensure_ascii=False), encoding="utf-8")
    fixed = experiments.load_slots(path)
    batch_id = batch.run_batch(fixed_slots=fixed, **batch_models())
    assert slot_rows(tmp_db, batch_id) == [(s["bucket"], s["topic"], s["format"], s["question_type"]) for s in chosen]
    statuses = {r[0] for r in tmp_db.execute("SELECT status FROM questions WHERE batch_id = ?", (batch_id,))}
    assert statuses == {"passed"}


def test_same_slots_give_same_batch_slots_in_two_arm_dbs(tmp_path, monkeypatch):
    fixed = pilot_slots()[:2]
    seen = []
    for arm in ("control", "arena"):
        path = tmp_path / f"{arm}.db"
        monkeypatch.setenv("QUIZ_DB", str(path))
        batch_id = batch.run_batch(fixed_slots=fixed, **batch_models())
        with db.connect(path) as conn:
            seen.append(slot_rows(conn, batch_id))
    assert seen[0] == seen[1] and len(seen[0]) == 2


def test_fixed_slots_resume(tmp_db):
    fixed = pilot_slots()
    first = batch_models(fail_from=3)
    batch_id = batch.run_batch(fixed_slots=fixed, workers=1, **first)
    assert batch.unfinished(batch_id) == 4
    second = batch_models()
    assert batch.run_batch(resume=batch_id, **second) == batch_id
    assert batch.unfinished(batch_id) == 0
    assert len(second["gen_model"].prompts) == 4


def test_fixed_slots_reject_unknown_topic(tmp_path):
    bad = pilot_slots()[:1]
    bad[0] = bad[0] | {"topic": "no such topic"}
    path = tmp_path / "slots.json"
    path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        experiments.load_slots(path)


def test_fixed_slots_reject_changed_pages(tmp_path):
    bad = pilot_slots()[:1]
    bad[0] = bad[0] | {"pages": ["/somewhere/else"]}
    path = tmp_path / "slots.json"
    path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        experiments.load_slots(path)


def test_cli_generate_slots_argument(tmp_path):
    p = build_parser()
    a = p.parse_args(["generate", "--slots", "s.json"])
    assert (a.slots, a.plan, a.resume) == ("s.json", None, None)
    a = p.parse_args(["generate", "--slots", "s.json", "--count", "2"])
    assert a.count == 2
    with pytest.raises(SystemExit):
        p.parse_args(["generate", "--slots", "s.json", "--plan", "pilot"])


def test_cli_generate_refuses_default_db_for_experiment(tmp_path, monkeypatch):
    """`--slots`나 `QUIZ_PROMPTS_DIR`을 쓰면 실험이다. `data/quiz.db`에 쓰지 않는다."""
    monkeypatch.delenv("QUIZ_DB", raising=False)
    called = []
    monkeypatch.setattr(batch, "run_batch", lambda **k: called.append(k))
    path = tmp_path / "slots.json"
    path.write_text(json.dumps(pilot_slots()[:1], ensure_ascii=False), encoding="utf-8")
    assert main(["generate", "--slots", str(path)]) == 1
    monkeypatch.setenv(prompts.ENV, str(tmp_path))
    assert main(["generate", "--plan", "pilot"]) == 1
    assert called == []


# --- quiz experiment judge ---

def table_counts(path) -> dict[str, int]:
    conn = sqlite3.connect(path)
    try:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        return {n: conn.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0] for n in names}
    finally:
        conn.close()


def digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def db_question():
    """make_question이 넣는 문제를 파이프라인 모양으로 만든다(인라인 문항용)."""
    return {
        "format": "single", "stem_en": "Injected copy: what does StateGraph do?",
        "choices": [{"id": c, "text": f"choice {c}"} for c in "ABCD"], "answer_key": ["C"],
        "explanation_ko": "해설", "cca_f_tag": "n/a",
        "segments": [{"segment_id": "s1", "en": "What does StateGraph do?", "ko": "StateGraph는 무엇을 하나?"}],
        "grounding_records": [{"page": "/oss/python/langgraph/graph-api", "quote": "q" * 40, "answer_basis": "근거"}],
    }


ITEMS = [
    {"item_id": "real-001", "source": "db", "question_id": QID,
     "label": {"defect_type": "explanation_error", "origin": "real", "note": "LABEL-SECRET-1"}},
    {"item_id": "inj-001", "source": "inline", "question_id": QID, "question": db_question(),
     "label": {"defect_type": "answer_key", "origin": "injected", "seed": 11}},
    {"item_id": "ok-001", "source": "db", "question_id": QID,
     "label": {"defect_type": None, "subset": "audit_clean"}},
    {"item_id": "ok-002", "source": "db", "question_id": QID,
     "label": {"defect_type": None, "subset": "crosscheck_clean"}},
]

FAIL_KEY = PASS | {"answer_key_correct": False, "verdict": "fail", "reasons": ["wrong key"]}


class ByItem(FakeModel):
    """프롬프트 내용으로 판정을 고른다. 인라인 문항(결함 주입 사본)은 실패시킨다."""

    def __init__(self, fail_all=False):
        super().__init__(None)
        self.fail_all = fail_all

    def next_payload(self):
        prompt = self.prompts[-1]
        return FAIL_KEY if self.fail_all or "Injected copy" in prompt else PASS


@pytest.fixture
def judge_setup(tmp_db, tmp_path, exp_dir):
    make_question(tmp_db, QID, answer_key=("B",))
    tmp_db.commit()
    items = tmp_path / "items.json"
    items.write_text(json.dumps({"items": ITEMS}, ensure_ascii=False), encoding="utf-8")
    return items


def test_experiment_judge_writes_arm_file_and_keeps_quiz_db(judge_setup, tmp_db, exp_dir):
    path = db.db_path()
    before_counts, before_hash = table_counts(path), digest(path)
    model = ByItem()
    out = experiments.run_judge(judge_setup, "control", model=model, model_id="fake-judge", workers=1)
    assert out == exp_dir / "EXP-1" / "control.json"
    assert table_counts(path) == before_counts and digest(path) == before_hash

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["arm"] == "control" and data["exp"] == "EXP-1" and data["model"] == "fake-judge"
    assert data["prompts_dir"] == str(prompts.prompt_dir())
    assert data["allowlist_sha256"] == hashlib.sha256(allowlist.ALLOWLIST_PATH.read_bytes()).hexdigest()
    res = {r["item_id"]: r for r in data["results"]}
    assert list(res) == [i["item_id"] for i in ITEMS]
    assert res["inj-001"]["rejected"] is True
    assert res["inj-001"]["fail_reasons"] == ["judge_fail:answer_key_correct"]
    assert res["real-001"]["rejected"] is False and res["real-001"]["fail_reasons"] == []
    for r in res.values():
        assert set(experiments.RESULT_KEYS) <= set(r)
        assert (r["input_tokens"], r["output_tokens"]) == (100, 20)
        assert r["latency_s"] >= 0 and r["error"] is None
        assert r["pages"] == ["/oss/python/langgraph/graph-api"]
    assert res["real-001"]["label"] == ITEMS[0]["label"]
    # 라벨은 Judge에게 보이지 않는다
    assert not any("LABEL-SECRET-1" in p or "explanation_error" in p for p in model.prompts)
    # 문항의 근거 페이지 스냅샷 원문을 Judge에게 준다
    assert "<document page=\"/oss/python/langgraph/graph-api\">" in model.prompts[0]


def test_experiment_judge_opens_quiz_db_read_only(judge_setup):
    conn = experiments.connect_ro(db.db_path())
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM questions")
    conn.close()


def test_experiment_judge_resume_skips_done_items(judge_setup, exp_dir):
    class Boom(FakeModel):
        def __init__(self):
            super().__init__(PASS)

        def next_payload(self):
            if "Injected copy" in self.prompts[-1]:
                raise RuntimeError("throttled")
            return PASS

    first = experiments.run_judge(judge_setup, "control", model=Boom(), model_id="fake-judge", workers=1)
    res = {r["item_id"]: r for r in json.loads(first.read_text(encoding="utf-8"))["results"]}
    assert res["inj-001"]["error"].startswith("RuntimeError")
    again = ByItem()
    experiments.run_judge(judge_setup, "control", model=again, model_id="fake-judge", workers=1)
    assert len(again.prompts) == 1  # 오류난 1문항만 다시 돈다
    res = {r["item_id"]: r for r in json.loads(first.read_text(encoding="utf-8"))["results"]}
    assert res["inj-001"]["error"] is None and res["inj-001"]["rejected"] is True


def test_experiment_judge_refuses_resume_with_other_model(judge_setup):
    experiments.run_judge(judge_setup, "control", model=ByItem(), model_id="fake-judge", workers=1)
    with pytest.raises(experiments.ExperimentError):
        experiments.run_judge(judge_setup, "control", model=ByItem(), model_id="other-model", workers=1)


def test_experiment_judge_uses_extra_items(judge_setup, prompt_copy, exp_dir):
    write_extra(prompt_copy)
    model = FakeModel(PASS | {"explanation_correct": False, "verdict": "fail", "reasons": ["x"]})
    out = experiments.run_judge(judge_setup, "arena", model=model, model_id="fake-judge", workers=1)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["extra_items"] == ["explanation_correct"]
    assert all(r["fail_reasons"] == ["judge_fail:explanation_correct"] for r in data["results"])


@pytest.mark.parametrize("bad", [
    [{"item_id": "a", "source": "db"}],                                  # question_id 없음
    [{"item_id": "a", "source": "inline", "question": {"stem_en": "x"}}],  # format 없음
    [{"item_id": "a", "source": "web", "question_id": QID}],
    [{"item_id": "a", "source": "db", "question_id": QID}, {"item_id": "a", "source": "db", "question_id": QID}],
])
def test_items_file_validation(tmp_path, bad):
    path = tmp_path / "items.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(experiments.ExperimentError):
        experiments.load_items(path)


def test_cli_experiment_arguments():
    p = build_parser()
    a = p.parse_args(["experiment", "judge", "--items", "i.json", "--arm", "control"])
    assert (a.items, a.arm, a.model, a.exp) == ("i.json", "control", None, "EXP-1")
    a = p.parse_args(["experiment", "judge", "--items", "i.json", "--arm", "haiku",
                      "--model", "global.anthropic.claude-haiku-4-5-20251001-v1:0"])
    assert a.model == "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    a = p.parse_args(["experiment", "summary", "--exp", "EXP-1", "--compare", "control,control-2"])
    assert (a.exp, a.compare) == ("EXP-1", "control,control-2")
    with pytest.raises(SystemExit):
        p.parse_args(["experiment", "judge", "--items", "i.json"])


# --- (3) summary ---

def test_summary_exp1_tables_have_columns(judge_setup, exp_dir, capsys):
    experiments.run_judge(judge_setup, "control", model=ByItem(), model_id="fake-judge", workers=1)
    experiments.run_judge(judge_setup, "strict", model=ByItem(fail_all=True), model_id="fake-judge", workers=1)
    # 같은 디렉토리의 items.json 같은 arm 아닌 파일은 무시한다
    (exp_dir / "EXP-1" / "items.json").write_text(json.dumps({"items": ITEMS}), encoding="utf-8")

    s = experiments.summary("EXP-1", compare=("control", "strict"))
    assert [t["name"] for t in s["tables"]] == ["detection", "false_reject", "cost", "flips"]
    tables = {t["name"]: t for t in s["tables"]}
    for name, cols in experiments.EXP1_COLUMNS.items():
        assert tables[name]["columns"] == list(cols)

    det = {(r["arm"], r["origin"], r["defect_type"]): r for r in tables["detection"]["rows"]}
    assert (det[("control", "injected", "answer_key")]["detected"], det[("control", "injected", "answer_key")]["total"]) == (1, 1)
    assert det[("control", "real", "explanation_error")]["detected"] == 0
    assert det[("strict", "real", "explanation_error")]["detected"] == 1
    fr = {(r["arm"], r["subset"]): r for r in tables["false_reject"]["rows"]}
    assert fr[("control", "audit_clean")]["rejected"] == 0 and fr[("strict", "audit_clean")]["rejected"] == 1
    assert fr[("strict", "crosscheck_clean")]["total"] == 1
    cost = {r["arm"]: r for r in tables["cost"]["rows"]}
    assert cost["control"]["calls"] == 4 and cost["control"]["input_tokens_per_call"] == 100
    flips = tables["flips"]["rows"][0]
    assert (flips["arm_a"], flips["arm_b"], flips["compared"], flips["flips"]) == ("control", "strict", 4, 3)

    assert main(["experiment", "summary", "--exp", "EXP-1"]) == 0
    printed = capsys.readouterr().out
    for cols in experiments.EXP1_COLUMNS.values():
        if cols is experiments.EXP1_COLUMNS["flips"]:
            continue
        assert "| " + " | ".join(cols) + " |" in printed


class QuoteOnce:
    """슬롯마다 첫 시도는 quote_mismatch, 재시도는 통과시키는 게이트(workers=1 기준)."""

    def __init__(self):
        self.calls = 0

    def __call__(self, *a, **k):
        self.calls += 1
        return ["quote_mismatch"] if self.calls % 2 == 1 else []


def test_summary_exp2_reuses_metrics_and_has_columns(tmp_path, exp_dir, monkeypatch):
    prod = tmp_path / "quiz.db"
    monkeypatch.setenv("QUIZ_DB", str(prod))
    with db.connect(prod) as conn:
        from quiz.migrate import apply_migrations
        apply_migrations(conn)
        make_question(conn, QID)
    before = table_counts(prod)

    fixed = pilot_slots()[:2]
    for arm in ("control", "arena"):
        arm_db = exp_dir / "EXP-2" / f"{arm}.db"
        monkeypatch.setenv("QUIZ_DB", str(arm_db))
        m = batch_models() | {"gate_fn": QuoteOnce()}
        batch.run_batch(fixed_slots=fixed, workers=1, **m)
    assert table_counts(prod) == before

    called = []
    real = experiments.metrics.build
    monkeypatch.setattr(experiments.metrics, "build", lambda conn: called.append(1) or real(conn))
    s = experiments.summary("EXP-2")
    assert len(called) == 2
    table = s["tables"][0]
    assert table["columns"] == list(experiments.EXP2_COLUMNS)
    rows = {r["arm"]: r for r in table["rows"]}
    assert list(rows) == ["arena", "control"]
    r = rows["control"]
    assert (r["slots"], r["passed"]) == (2, 2)
    assert (r["first_quote_match"], r["first_attempts"]) == (0, 2)
    assert (r["retry_quote_pass"], r["retries_after_quote_mismatch"]) == (2, 2)
    assert r["judge_pass_rate"] == 1.0 and r["t2_11_fails"] == 0
    assert r["drops"] == {}
    assert r["seconds"] is not None
