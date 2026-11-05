"""파이프라인 노드(design.md 6.1). 상태는 슬롯 1개다."""

import json
from typing import Any, TypedDict

from quiz import gates, llm
from quiz.pipeline import prompts
from quiz.pipeline.schemas import GeneratedQuestion, JudgeVerdict

JUDGE_ITEMS = ("answer_key_correct", "quote_supports_answer", "distractors_wrong", "mapping_faithful")


class SlotState(TypedDict, total=False):
    slot: dict            # bucket, topic, format, question_type, page
    snapshot: str         # 허용 목록 스냅샷 원문
    allowed_pages: set[str]
    feedback: list[str]   # 직전 실패 이유
    question: dict | None
    judge: dict | None
    gate_fails: list[str]
    fail_reasons: list[str]
    tokens: dict          # {"input": int, "output": int}


def _add_tokens(state: SlotState, raw) -> dict:
    i, o = llm.usage(raw)
    t = dict(state.get("tokens") or {"input": 0, "output": 0})
    t["input"] += i
    t["output"] += o
    return t


def generate(state: SlotState, model=None) -> dict[str, Any]:
    slot = state["slot"]
    feedback = state.get("feedback") or []
    fb = ""
    if feedback:
        fb = "## Previous attempt failed\n\n" + "\n".join(f"- {r}" for r in feedback) + "\n\nFix these problems."
    prompt = prompts.render(
        "generate",
        bucket=slot["bucket"], topic=slot["topic"], format=slot["format"],
        question_type=slot["question_type"], page=slot["page"],
        feedback=fb, document=state["snapshot"],
    )
    model = model or llm.gen_model()
    out = model.with_structured_output(GeneratedQuestion, include_raw=True).invoke(prompt)
    tokens = _add_tokens(state, out["raw"])
    if out.get("parsed") is None:
        return {"question": None, "fail_reasons": ["schema_invalid"], "tokens": tokens}
    return {"question": out["parsed"].model_dump(), "fail_reasons": [], "tokens": tokens}


def judge(state: SlotState, model=None) -> dict[str, Any]:
    question = state.get("question")
    if question is None:
        return {"judge": None}
    prompt = prompts.render(
        "judge",
        question=json.dumps(question, ensure_ascii=False, indent=2),
        page=state["slot"]["page"], document=state["snapshot"],
    )
    model = model or llm.judge_model()
    out = model.with_structured_output(JudgeVerdict, include_raw=True).invoke(prompt)
    tokens = _add_tokens(state, out["raw"])
    fails = list(state.get("fail_reasons", []))
    if out.get("parsed") is None:
        return {"judge": None, "fail_reasons": fails + ["judge_fail:schema_invalid"], "tokens": tokens}
    verdict = out["parsed"].model_dump()
    fails += [f"judge_fail:{item}" for item in JUDGE_ITEMS if not verdict[item]]
    return {"judge": verdict, "fail_reasons": fails, "tokens": tokens}


def run_gates(state: SlotState) -> dict[str, Any]:
    question = state.get("question")
    if question is None:
        return {"gate_fails": []}
    page = state["slot"]["page"]
    fails = gates.run_gates(question, {page: state["snapshot"]}, state["allowed_pages"])
    return {"gate_fails": fails, "fail_reasons": list(state.get("fail_reasons", [])) + fails}
