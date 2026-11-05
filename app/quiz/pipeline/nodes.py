"""파이프라인 노드(design.md 6.1). 상태는 슬롯 1개다."""

import json
import operator
from typing import Annotated, Any, TypedDict

from quiz import gates, llm, pricing, sandbox_client
from quiz.pipeline import prompts
from quiz.pipeline.schemas import SCHEMAS, JudgeVerdict

CODE_FORMAT = "code"
SHORT_FORMAT = "short"
JUDGE_ITEMS = ("answer_key_correct", "quote_supports_answer", "distractors_wrong", "mapping_faithful")
# 선택형(single, multi, code)에만 보는 출제 품질 항목(T2.11)
CHOICE_JUDGE_ITEMS = ("distractors_plausible", "no_cue")
DOCS_BASE = "https://docs.langchain.com"
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
    tokens: dict          # {"input": int, "output": int}. 시도 1회분
    exec_result: list[dict] | None
    exec_match: int | None
    duplicate_of: str | None
    peers: list[dict]     # 같은 버킷 passed 문제(dedupe 비교 대상)
    regen_count: int      # 0~3
    attempts: Annotated[list[dict], operator.add]  # 시도마다 1개. verification_results 1행이 된다
    status: str           # passed | dropped. 끝났을 때만 있다
    drop_reason: str | None


def _add_tokens(state: SlotState, raw, model, model_id: str | None = None) -> dict:
    """시도 1회분 토큰과 비용을 더한다. 단가 없는 모델을 한 번이라도 쓰면 비용은 None이다.

    `model_id`는 실제로 부른 모델이다(프로필 전환 모델). 없으면 `model.model_id`를 쓴다.
    """
    i, o = llm.usage(raw)
    t = dict(state.get("tokens") or {"input": 0, "output": 0})
    t["input"] += i
    t["output"] += o
    call = pricing.cost(model_id or getattr(model, "model_id", None), i, o)
    prev = t.get("cost_usd", 0.0)
    t["cost_usd"] = None if prev is None or call is None else prev + call
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
        quality_rules=prompts.load("quality/short" if fmt == SHORT_FORMAT else "quality/choice").strip(),
        feedback=_feedback(state.get("feedback") or []),
        documents=_documents(snapshots),
    )
    model = model or llm.gen_model()
    out = model.with_structured_output(SCHEMAS[fmt], include_raw=True).invoke(prompt)
    tokens = _add_tokens(state, out["raw"], model, out.get("model_id"))
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


JUDGE_RULE_FORMATS = (SHORT_FORMAT, CODE_FORMAT)
HIDDEN_FROM_JUDGE = ("fetched_at", "doc_url", "lock_hash")


def _judge_view(question: dict) -> dict:
    """Judge에게 보일 문제. 코드형 기대값(`expected`)은 숨긴다. 예측이 기대값을 베끼지 않게 한다."""
    view = {k: v for k, v in question.items() if k not in HIDDEN_FROM_JUDGE}
    if view.get("exec_spec"):
        view["exec_spec"] = [{"choice_id": c["choice_id"], "code": c["code"]} for c in view["exec_spec"]]
    return view


def merge_variants(accepted: list[str], variants: list[str]) -> list[str]:
    """Judge가 찾은 단답 변형을 보탠다. 정규화해서 같으면 넣지 않는다. 합쳐서 최대 5개다(GR-3)."""
    out = list(accepted)
    seen = {gates.normalize_short_answer(a) for a in out}
    for v in variants:
        key = gates.normalize_short_answer(v)
        if len(out) >= gates.MAX_ACCEPTED_ANSWERS:
            break
        if key and key not in seen:
            out.append(v.strip())
            seen.add(key)
    return out


def _judge_rules(fmt: str) -> str:
    parts = [] if fmt == SHORT_FORMAT else [prompts.load("judge/choice").strip()]
    if fmt in JUDGE_RULE_FORMATS:
        parts.append(prompts.load(f"judge/{fmt}").strip())
    return "\n\n".join(parts)


def judge_items(fmt: str) -> tuple[str, ...]:
    return JUDGE_ITEMS if fmt == SHORT_FORMAT else JUDGE_ITEMS + CHOICE_JUDGE_ITEMS


def judge(state: SlotState, model=None) -> dict[str, Any]:
    question = state.get("question")
    if question is None:
        return {"judge": None}
    fmt = state["slot"]["format"]
    snapshots = state["snapshots"]
    prompt = prompts.render(
        "judge",
        question=json.dumps(_judge_view(question), ensure_ascii=False, indent=2),
        format_rules=_judge_rules(fmt),
        page=", ".join(snapshots), document=_documents(snapshots),
    )
    model = model or llm.judge_model()
    out = model.with_structured_output(JudgeVerdict, include_raw=True).invoke(prompt)
    tokens = _add_tokens(state, out["raw"], model, out.get("model_id"))
    fails = list(state.get("fail_reasons", []))
    if out.get("parsed") is None:
        return {"judge": None, "fail_reasons": fails + ["judge_fail:schema_invalid"], "tokens": tokens}
    verdict = out["parsed"].model_dump()
    fails += [f"judge_fail:{item}" for item in judge_items(fmt) if not verdict[item]]
    result = {"judge": verdict, "fail_reasons": fails, "tokens": tokens}
    if fmt == SHORT_FORMAT and verdict["missing_variants"]:
        accepted = merge_variants(question.get("accepted_answers") or [], verdict["missing_variants"])
        result["question"] = {**question, "accepted_answers": accepted}
    return result


EXEC_FAIL_ORDER = ("version_conflict", "sandbox_module_missing", "judge_exec_mismatch")


def execute(state: SlotState, run=None) -> dict[str, Any]:
    """코드형 보기마다 샌드박스에서 실행하고 Judge 예측, 문서 기준 기대값과 비교한다(8.2)."""
    question = state.get("question")
    if question is None or state["slot"]["format"] != CODE_FORMAT:
        return {}
    run = run or sandbox_client.run
    preds = {p["choice_id"]: p for p in (state.get("judge") or {}).get("exec_predictions") or []}
    results, found = [], set()
    for case in question.get("exec_spec") or []:
        actual = run(case["code"])
        results.append({"choice_id": case["choice_id"], **actual})
        if (reason := sandbox_client.compare(actual, case["expected"], preds.get(case["choice_id"]))):
            found.add(reason)
    fails = [r for r in EXEC_FAIL_ORDER if r in found]
    return {
        "question": {**question, "lock_hash": sandbox_client.lock_hash()},
        "exec_result": results,
        "exec_match": int(not fails),
        "fail_reasons": list(state.get("fail_reasons", [])) + fails,
    }


def run_gates(state: SlotState, gate_fn=None) -> dict[str, Any]:
    question = state.get("question")
    if question is None:
        return {"gate_fails": []}
    snapshots = state["snapshots"]
    # 슬롯에 준 페이지만 대조할 수 있다. 다른 허용 페이지를 인용하면 page_not_allowed로 본다
    allowed = set(state["allowed_pages"]) & set(snapshots)
    fails = (gate_fn or gates.run_gates)(question, snapshots, allowed, fmt=state["slot"]["format"])
    return {"gate_fails": fails, "fail_reasons": list(state.get("fail_reasons", [])) + fails}


def dedupe(state: SlotState) -> dict[str, Any]:
    """같은 버킷 passed 문제와 비교한다. 같은 quote 또는 본문 Jaccard >= 0.6이면 `duplicate`다(4.4)."""
    question = state.get("question")
    if question is None:
        return {"duplicate_of": None}
    reason, dup = gates.check_duplicate(question, state.get("peers") or [])
    if reason is None:
        return {"duplicate_of": None}
    return {"duplicate_of": dup, "fail_reasons": list(state.get("fail_reasons", [])) + [reason]}


MAX_REGEN = 3
NO_REGEN = ("version_conflict", "duplicate")  # 재생성 없이 버린다(6.1 판정 규칙)
ATTEMPT_KEYS = ("question", "judge", "gate_fails", "fail_reasons", "tokens", "exec_result", "exec_match",
                "duplicate_of")


def decide(state: SlotState) -> tuple[str, str | None]:
    """(passed | dropped | regen, drop_reason)."""
    fails = state.get("fail_reasons") or []
    if not fails:
        return "passed", None
    for reason in NO_REGEN:
        if reason in fails:
            return "dropped", reason
    if (state.get("regen_count") or 0) >= MAX_REGEN:
        return "dropped", "regen_exhausted"
    return "regen", None


def record(state: SlotState) -> dict[str, Any]:
    """이번 시도를 `attempts`에 남기고 판정한다. 끝났으면 `status`를 채운다."""
    out: dict[str, Any] = {"attempts": [{k: state.get(k) for k in ATTEMPT_KEYS}]}
    status, reason = decide(state)
    if status != "regen":
        out |= {"status": status, "drop_reason": reason}
    return out


# sandbox/pyproject.toml 의존성과 맞춘다.
SANDBOX_HINT = ("A code choice imported a module that is not installed in the sandbox. Use only the Python "
                "standard library and these packages: langchain, langgraph, langchain-core, "
                "langchain-text-splitters, numpy, mcp, fastmcp, langchain-mcp-adapters.")


def feedback(state: SlotState) -> dict[str, Any]:
    """실패 이유(Judge 사유 포함)를 다음 생성 입력에 넣고 시도별 값을 비운다."""
    reasons = list(state.get("fail_reasons") or [])
    if "sandbox_module_missing" in reasons:
        reasons.append(SANDBOX_HINT)
    reasons += [f"judge: {r}" for r in (state.get("judge") or {}).get("reasons") or []]
    return {
        "feedback": reasons, "regen_count": (state.get("regen_count") or 0) + 1,
        "question": None, "judge": None, "gate_fails": [], "fail_reasons": [],
        "tokens": {"input": 0, "output": 0}, "exec_result": None, "exec_match": None, "duplicate_of": None,
    }
