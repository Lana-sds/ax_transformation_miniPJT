"""generate 노드 4형식(T2.1, design.md 6.1). 모델은 가짜로 바꾼다. Bedrock을 부르지 않는다."""

import pytest
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from quiz.pipeline import nodes, schemas

PAGE = "/oss/python/langgraph/graph-api"
PAGE2 = "/oss/python/langgraph/use-graph-api"
REF = "https://reference.langchain.com/python/langgraph/graph/StateGraph"

COMMON = {
    "stem_en": "What does StateGraph do?",
    "explanation_ko": "StateGraph는 상태 그래프를 만든다.",
    "segments": [{"segment_id": "s1", "en": "What does StateGraph do?", "ko": "StateGraph는 무엇을 하나?"}],
    "grounding_records": [{"page": PAGE, "quote": "q" * 40, "answer_basis": "근거"}],
    "cca_f_tag": "n/a",
}


def payload(fmt: str) -> dict:
    if fmt == "single":
        return {**COMMON, "choices": [{"id": c, "text": f"t{c}"} for c in "ABCD"], "answer_key": ["B"]}
    if fmt == "multi":
        return {**COMMON, "choices": [{"id": c, "text": f"t{c}"} for c in "ABCDE"],
                "answer_key": ["A", "C"], "select_count": 2}
    if fmt == "short":
        return {**COMMON, "answer_key": ["add_node"], "accepted_answers": ["add_node", "StateGraph.add_node"]}
    if fmt == "code":
        return {**COMMON,
                "choices": [{"id": c, "code": f"print('{c}')"} for c in "ABCD"],
                "answer_key": ["C"],
                "exec_spec": [{"choice_id": c, "code": f"print('{c}')",
                               "expected": {"ok": True, "stdout": f"{c}\n", "error_type": None}} for c in "ABCD"]}
    raise ValueError(fmt)


FORMATS = ["single", "multi", "short", "code"]


# --- 스키마 ---

@pytest.mark.parametrize("fmt", FORMATS)
def test_schema_accepts_valid_payload(fmt):
    schemas.SCHEMAS[fmt].model_validate(payload(fmt))


def test_single_rejects_answer_key_outside_choices():
    p = payload("single") | {"answer_key": ["E"]}
    with pytest.raises(ValidationError):
        schemas.SCHEMAS["single"].model_validate(p)


def test_single_rejects_two_answers():
    p = payload("single") | {"answer_key": ["A", "B"]}
    with pytest.raises(ValidationError):
        schemas.SCHEMAS["single"].model_validate(p)


def test_multi_requires_select_count_equal_to_answer_key():
    p = payload("multi") | {"select_count": 3}
    with pytest.raises(ValidationError):
        schemas.SCHEMAS["multi"].model_validate(p)


def test_multi_requires_two_or_more_answers():
    p = payload("multi") | {"answer_key": ["A"], "select_count": 1}
    with pytest.raises(ValidationError):
        schemas.SCHEMAS["multi"].model_validate(p)


def test_short_requires_answer_key_among_accepted_answers():
    p = payload("short") | {"answer_key": ["compile"]}
    with pytest.raises(ValidationError):
        schemas.SCHEMAS["short"].model_validate(p)


def test_code_requires_exec_spec_for_every_choice():
    p = payload("code")
    p["exec_spec"] = p["exec_spec"][:3]
    with pytest.raises(ValidationError):
        schemas.SCHEMAS["code"].model_validate(p)


def test_cca_f_tag_is_closed_set():
    p = payload("single") | {"cca_f_tag": "kubernetes"}
    with pytest.raises(ValidationError):
        schemas.SCHEMAS["single"].model_validate(p)


# --- 노드 ---

class FakeStructured:
    def __init__(self, parent, schema):
        self.parent, self.schema = parent, schema

    def invoke(self, prompt):
        self.parent.prompts.append(prompt)
        self.parent.schemas.append(self.schema)
        raw = AIMessage(content="", usage_metadata={"input_tokens": 100, "output_tokens": 20, "total_tokens": 120})
        if self.parent.payload is None:
            return {"raw": raw, "parsed": None, "parsing_error": ValueError("bad")}
        return {"raw": raw, "parsed": self.schema.model_validate(self.parent.payload), "parsing_error": None}


class FakeModel:
    def __init__(self, payload):
        self.payload = payload
        self.prompts: list[str] = []
        self.schemas: list[type] = []

    def with_structured_output(self, schema, include_raw=False):
        assert include_raw
        return FakeStructured(self, schema)


def state(fmt: str, near: bool = False, pages=(PAGE, PAGE2)) -> dict:
    return {
        "slot": {"bucket": "langgraph_basics", "topic": "StateGraph", "format": fmt,
                 "question_type": "concept", "pages": list(pages), "near": near,
                 "near_pages": [PAGE2] if near else []},
        "snapshots": {p: f"DOC-{p}" for p in pages},
        "fetched": {p: "2026-11-05" for p in pages},
        "allowed_pages": set(pages),
    }


@pytest.mark.parametrize("fmt", FORMATS)
def test_generate_uses_format_schema(fmt):
    model = FakeModel(payload(fmt))
    out = nodes.generate(state(fmt), model)
    assert model.schemas == [schemas.SCHEMAS[fmt]]
    assert out["fail_reasons"] == []
    assert out["question"]["format"] == fmt
    assert out["question"]["fetched_at"] == "2026-11-05"
    assert out["tokens"] == {"input": 100, "output": 20}


def test_generate_prompt_has_every_page_and_format_rules():
    model = FakeModel(payload("multi"))
    nodes.generate(state("multi"), model)
    prompt = model.prompts[0]
    for p in (PAGE, PAGE2):
        assert f"DOC-{p}" in prompt
        assert p in prompt
    assert "select_count" in prompt
    assert "{{" not in prompt


@pytest.mark.parametrize("fmt", FORMATS)
def test_generate_prompt_has_rules_for_its_format_only(fmt):
    model = FakeModel(payload(fmt))
    nodes.generate(state(fmt), model)
    prompt = model.prompts[0]
    marker = {"single": "Format `single`", "multi": "Format `multi`", "short": "Format `short`", "code": "Format `code`"}
    for f, m in marker.items():
        assert (m in prompt) == (f == fmt)


def test_generate_near_topic_adds_prohibition():
    model = FakeModel(payload("single"))
    nodes.generate(state("single", near=True), model)
    assert nodes.NEAR_RULE in model.prompts[0]
    model = FakeModel(payload("single"))
    nodes.generate(state("single", near=False), model)
    assert nodes.NEAR_RULE not in model.prompts[0]


def test_generate_code_sets_doc_url_from_first_grounding_page():
    model = FakeModel(payload("code"))
    out = nodes.generate(state("code"), model)
    assert out["question"]["doc_url"] == "https://docs.langchain.com" + PAGE


def test_doc_url_keeps_reference_url():
    assert nodes.doc_url(REF) == REF
    assert nodes.doc_url(PAGE) == "https://docs.langchain.com" + PAGE


def test_generate_non_code_has_no_doc_url():
    out = nodes.generate(state("single"), FakeModel(payload("single")))
    assert out["question"].get("doc_url") is None


def test_generate_multi_keeps_select_count():
    out = nodes.generate(state("multi"), FakeModel(payload("multi")))
    assert out["question"]["select_count"] == 2


def test_generate_parse_failure_is_schema_invalid():
    out = nodes.generate(state("single"), FakeModel(None))
    assert out["question"] is None
    assert out["fail_reasons"] == ["schema_invalid"]


def test_generate_feedback_goes_into_prompt():
    model = FakeModel(payload("single"))
    st = state("single") | {"feedback": ["quote_mismatch"]}
    nodes.generate(st, model)
    assert "quote_mismatch" in model.prompts[0]
