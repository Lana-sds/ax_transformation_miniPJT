"""파이프라인 노드(design.md 6.1). 상태는 슬롯 1개다."""

import json
from typing import Any, TypedDict

from quiz import gates, llm
from quiz.pipeline import prompts
from quiz.pipeline.schemas import SCHEMAS, JudgeVerdict

JUDGE_ITEMS = ("answer_key_correct", "quote_supports_answer", "distractors_wrong", "mapping_faithful")
DOCS_BASE = "https://docs.langchain.com"
CODE_FORMAT = "code"
NEAR_RULE = prompts.load("near").strip()


class SlotState(TypedDict, total=False):
    slot: dict            # bucket, topic, format, question_type, pages, near, near_pages
    snapshots: dict       # {page: 스냅샷 원문}. 슬롯 근거 페이지만
    fetched: dict         # {page: 조회 날짜}
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


def doc_url(page: str) -> str:
    """코드형 "코드 보기" 링크(FR-2.4). 문서 경로는 docs.langchain.com 주소로, API 레퍼런스는 그대로 둔다."""
    return page if page.startswith("http") else DOCS_BASE + page


def _documents(snapshots: dict[str, str]) -> str:
    return "\n\n".join(f'<document page="{p}">\n{text}\n</document>' for p, text in snapshots.items())


def _format_rules(fmt: str) -> str:
    rules = prompts.load(f"formats/{fmt}").strip()
    if fmt == CODE_FORMAT:
        rules = rules.replace("{{fakes}}", prompts.load("fakes").strip())
    return rules


def _feedback(feedback: list[str]) -> str:
    if not feedback:
        return ""
    return "## Previous attempt failed\n\n" + "\n".join(f"- {r}" for r in feedback) + "\n\nFix these problems."


def generate(state: SlotState, model=None) -> dict[str, Any]:
    slot = state["slot"]
    fmt = slot["format"]
    snapshots = state["snapshots"]
    prompt = prompts.render(
        "generate",
        bucket=slot["bucket"], topic=slot["topic"], format=fmt, question_type=slot["question_type"],
        pages="\n".join(f"  - `{p}`" for p in snapshots),
        near_rule=NEAR_RULE if slot.get("near") else "",
        format_rules=_format_rules(fmt),
        feedback=_feedback(state.get("feedback") or []),
        documents=_documents(snapshots),
    )
    model = model or llm.gen_model()
    out = model.with_structured_output(SCHEMAS[fmt], include_raw=True).invoke(prompt)
    tokens = _add_tokens(state, out["raw"])
    if out.get("parsed") is None:
        return {"question": None, "fail_reasons": ["schema_invalid"], "tokens": tokens}
    question = out["parsed"].model_dump()
    question["format"] = fmt
    cited = [r["page"] for r in question["grounding_records"]]
    fetched = state.get("fetched") or {}
    dates = [fetched[p] for p in cited if p in fetched] or list(fetched.values())
    question["fetched_at"] = min(dates) if dates else None
    if fmt == CODE_FORMAT and cited:
        question["doc_url"] = doc_url(cited[0])
    return {"question": question, "fail_reasons": [], "tokens": tokens}


def judge(state: SlotState, model=None) -> dict[str, Any]:
    question = state.get("question")
    if question is None:
        return {"judge": None}
    snapshots = state["snapshots"]
    prompt = prompts.render(
        "judge",
        question=json.dumps(question, ensure_ascii=False, indent=2),
        page=", ".join(snapshots), document=_documents(snapshots),
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
    snapshots = state["snapshots"]
    # 슬롯에 준 페이지만 대조할 수 있다. 다른 허용 페이지를 인용하면 page_not_allowed로 본다
    allowed = set(state["allowed_pages"]) & set(snapshots)
    fails = gates.run_gates(question, snapshots, allowed, fmt=state["slot"]["format"])
    return {"gate_fails": fails, "fail_reasons": list(state.get("fail_reasons", [])) + fails}
