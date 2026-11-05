"""출제 품질 기준(T2.11). 생성 프롬프트 규칙 4개와 Judge 선택형 항목 2개."""

import pytest

from llm_fakes import FakeModel
from quiz.pipeline import nodes, schemas
from test_generate import FORMATS, payload, state
from test_judge import PASS, judged

CHOICE_FORMATS = ("single", "multi", "code")

# 규칙마다 프롬프트에 반드시 들어가는 문구
RULE_APPLIED = "Do not write a question that only asks to recall a definition"
RULE_PLAUSIBLE = "Each wrong choice must carry one plausible misconception"
RULE_NO_CUE = "No cues"
RULE_EXPLAIN_CHOICE = "one paragraph per choice"
RULE_EXPLAIN_SHORT = "why the canonical answer and every accepted answer are correct"


def generated_prompt(fmt: str) -> str:
    model = FakeModel(payload(fmt))
    nodes.generate(state(fmt), model)
    return model.prompts[0]


@pytest.mark.parametrize("fmt", FORMATS)
def test_every_format_prompt_asks_for_applied_question(fmt):
    assert RULE_APPLIED in generated_prompt(fmt)


@pytest.mark.parametrize("fmt", CHOICE_FORMATS)
def test_choice_prompt_has_all_four_rules(fmt):
    prompt = generated_prompt(fmt)
    for rule in (RULE_APPLIED, RULE_PLAUSIBLE, RULE_NO_CUE, RULE_EXPLAIN_CHOICE):
        assert rule in prompt
    assert RULE_EXPLAIN_SHORT not in prompt
    assert "{{" not in prompt


def test_short_prompt_has_no_distractor_or_cue_rule():
    prompt = generated_prompt("short")
    assert RULE_PLAUSIBLE not in prompt
    assert RULE_NO_CUE not in prompt
    assert RULE_EXPLAIN_CHOICE not in prompt
    assert RULE_EXPLAIN_SHORT in prompt
    assert "{{" not in prompt


def test_cue_rule_names_the_three_cues():
    prompt = generated_prompt("single")
    for cue in ("only", "always", "never", "longer"):
        assert cue in prompt


# --- Judge ---

def test_verdict_choice_items_are_required():
    # 선택 필드면 모델이 생략하고 기본값이 들어가 단서 문제도 통과했다(2026-11-05 실제 Judge)
    required = schemas.JudgeVerdict.model_json_schema()["required"]
    for item in nodes.CHOICE_JUDGE_ITEMS:
        assert item in required


@pytest.mark.parametrize("fmt", CHOICE_FORMATS)
@pytest.mark.parametrize("item", nodes.CHOICE_JUDGE_ITEMS)
def test_choice_item_false_becomes_fail_reason(fmt, item):
    verdict = PASS | {item: False, "verdict": "fail", "reasons": ["cue"]}
    if fmt == "code":
        verdict["exec_predictions"] = []
    out = nodes.judge(judged(fmt), FakeModel(verdict))
    assert f"judge_fail:{item}" in out["fail_reasons"]


def test_both_choice_items_false_give_both_reasons():
    verdict = PASS | {"distractors_plausible": False, "no_cue": False, "verdict": "fail", "reasons": ["a", "b"]}
    out = nodes.judge(judged("single"), FakeModel(verdict))
    assert out["fail_reasons"] == ["judge_fail:distractors_plausible", "judge_fail:no_cue"]


def test_short_ignores_choice_items():
    verdict = PASS | {"distractors_plausible": False, "no_cue": False}
    out = nodes.judge(judged("short"), FakeModel(verdict))
    assert out["fail_reasons"] == []


def test_existing_distractors_wrong_item_kept():
    assert "distractors_wrong" in nodes.JUDGE_ITEMS


@pytest.mark.parametrize("fmt", CHOICE_FORMATS)
def test_choice_judge_prompt_has_new_items(fmt):
    model = FakeModel(PASS)
    nodes.judge(judged(fmt), model)
    for item in nodes.CHOICE_JUDGE_ITEMS:
        assert f"`{item}`" in model.prompts[0]
    assert "{{" not in model.prompts[0]


def test_short_judge_prompt_has_no_choice_items():
    model = FakeModel(PASS)
    nodes.judge(judged("short"), model)
    for item in nodes.CHOICE_JUDGE_ITEMS:
        assert f"`{item}`" not in model.prompts[0]
