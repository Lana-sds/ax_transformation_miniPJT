"""judge 노드(T2.2, design.md 6.1). 모델은 가짜로 바꾼다."""

import json

import pytest

from llm_fakes import FakeModel
from quiz.pipeline import nodes, schemas
from test_generate import PAGE, payload, state

PASS = {"answer_key_correct": True, "quote_supports_answer": True, "distractors_wrong": True,
        "mapping_faithful": True, "distractors_plausible": True, "no_cue": True, "verdict": "pass", "reasons": []}


def judged(fmt: str, question: dict | None = None) -> dict:
    st = state(fmt, pages=(PAGE,))
    q = dict(question or payload(fmt))
    q["format"] = fmt
    st["question"] = q
    st["fail_reasons"] = []
    return st


def test_judge_verdict_defaults_extra_lists_to_empty():
    v = schemas.JudgeVerdict.model_validate(PASS)
    assert v.missing_variants == [] and v.exec_predictions == []


@pytest.mark.parametrize("item", nodes.JUDGE_ITEMS)
def test_judge_failed_item_becomes_fail_reason(item):
    verdict = PASS | {item: False, "verdict": "fail", "reasons": ["wrong"]}
    out = nodes.judge(judged("single"), FakeModel(verdict))
    assert out["fail_reasons"] == [f"judge_fail:{item}"]


def test_judge_wrong_answer_key_fails():
    verdict = PASS | {"answer_key_correct": False, "verdict": "fail", "reasons": ["B is correct, not C"]}
    q = payload("single") | {"answer_key": ["C"]}
    out = nodes.judge(judged("single", q), FakeModel(verdict))
    assert "judge_fail:answer_key_correct" in out["fail_reasons"]


def test_judge_schema_failure():
    out = nodes.judge(judged("single"), FakeModel(None))
    assert out["fail_reasons"] == ["judge_fail:schema_invalid"]


def test_judge_short_adds_missing_variants_up_to_five():
    q = payload("short") | {"accepted_answers": ["add_node", "StateGraph.add_node"]}
    verdict = PASS | {"missing_variants": ["add node", "ADD_NODE", "graph.add_node", "builder.add_node", "x.add_node"]}
    out = nodes.judge(judged("short", q), FakeModel(verdict))
    # "ADD_NODE"는 정규화하면 add_node와 같아 넣지 않는다. 합쳐서 5개까지다
    assert out["question"]["accepted_answers"] == [
        "add_node", "StateGraph.add_node", "add node", "graph.add_node", "builder.add_node"]


def test_judge_non_short_ignores_variants():
    verdict = PASS | {"missing_variants": ["x"]}
    out = nodes.judge(judged("single"), FakeModel(verdict))
    assert "accepted_answers" not in out.get("question", {})


def test_judge_prompt_has_format_rules():
    model = FakeModel(PASS)
    nodes.judge(judged("short"), model)
    assert "missing_variants" in model.prompts[0]
    model = FakeModel(PASS)
    nodes.judge(judged("code"), model)
    assert "exec_predictions" in model.prompts[0]
    model = FakeModel(PASS)
    nodes.judge(judged("single"), model)
    assert "missing_variants" not in model.prompts[0] and "exec_predictions" not in model.prompts[0]


def test_judge_code_does_not_see_expected_results():
    q = payload("code")
    q["exec_spec"][0]["expected"]["stdout"] = "SECRET-EXPECTED\n"
    model = FakeModel(PASS)
    nodes.judge(judged("code", q), model)
    assert "SECRET-EXPECTED" not in model.prompts[0]
    assert "print('A')" in model.prompts[0]


def test_judge_code_keeps_predictions():
    preds = [{"choice_id": c, "ok": True, "stdout": f"{c}\n", "error_type": None} for c in "ABCD"]
    out = nodes.judge(judged("code"), FakeModel(PASS | {"exec_predictions": preds}))
    assert [p["choice_id"] for p in out["judge"]["exec_predictions"]] == list("ABCD")


def test_judge_prompt_question_is_valid_json():
    model = FakeModel(PASS)
    nodes.judge(judged("multi"), model)
    body = model.prompts[0].split("<question>")[1].split("</question>")[0]
    assert json.loads(body)["select_count"] == 2
