"""교차 풀이 점검(T2.10, 요구사항 밖 보조 점검. 사용자 승인 2026-11-05).

Claude 계열이 아닌 모델 2개가 정답 키를 보지 않고 passed 문제를 푼다. 정답 키와 다른 답이 나온 문항을
정답 키 오류 후보로 보고 사용자가 T5.1 전에 검토한다.

- 모델에게 주는 값: `stem_en`, 보기, 형식, `select_count`, 근거 페이지 스냅샷 원문 전체.
- 주지 않는 값: 정답 키, 허용 답안, 해설, 매핑, quote, `answer_basis`.
- 코드형은 기본으로 건너뛴다. 샌드박스 실행이 독립 근거이기 때문이다.
- `openai.gpt-oss-120b-1:0`은 us-east-1에만 있다. 다른 리전이면 오류로 멈춘다.
- 결과는 `data/crosscheck/<대상 ID>.json`과 `.md` 요약 표다. DB와 문제 `status`는 바꾸지 않는다.
- 사용자 검토 값(`reviewed`: ok | key_error | weak_grounding | ambiguous)은 다시 돌려도 남긴다.
  `audit_records`에는 쓰지 않는다. 감사 통과 기준 계산에 섞이지 않게 한다.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import BaseModel, Field

from quiz import allowlist, db, grading, llm, store
from quiz.pipeline import prompts

MODELS = ("us.amazon.nova-pro-v1:0", "openai.gpt-oss-120b-1:0")
REQUIRED_REGION = "us-east-1"
OUT_DIR = db.REPO_ROOT / "data" / "crosscheck"
SKIP_FORMATS = ("code",)
WORKERS = 2
REVIEW_VALUES = ("ok", "key_error", "weak_grounding", "ambiguous")

FORMAT_RULES = {
    "single": "Choose exactly one choice. Put only its id in `answer`, for example `B`.",
    "multi": "Select {n} choices. Put their ids in `answer`, separated by commas, for example `A, D`.",
    "short": "Put one API, class, function or parameter name, or a single term in `answer`, for example `add_node`.",
    "code": "Choose exactly one code choice. Put only its id in `answer`, for example `C`.",
}


class CrosscheckRegionError(RuntimeError):
    pass


class CrossAnswer(BaseModel):
    unanswerable: bool = Field(description="True if the documentation does not let you decide")
    answer: str = Field(description="Choice ids separated by commas, e.g. 'A, D', or one short answer. "
                                    "Empty string only if unanswerable")
    supporting_sentence: str = Field(description="One verbatim sentence from the documentation that supports the answer")


def check_region() -> None:
    region = llm.region()
    if region != REQUIRED_REGION:
        raise CrosscheckRegionError(
            f"crosscheck needs {REQUIRED_REGION} (openai.gpt-oss-120b-1:0 is only there), got {region}")


def _question_text(q: dict) -> str:
    lines = [f"Format: {q['format']}", "", q["stem_en"]]
    if q.get("choices"):
        lines.append("")
        for c in q["choices"]:
            body = c.get("text") if c.get("text") is not None else c.get("code", "")
            lines.append(f"{c['id']}. {body}")
    return "\n".join(lines)


def build_prompt(q: dict, snapshots: dict[str, str]) -> str:
    """정답 키, 허용 답안, 해설, 매핑, quote, answer_basis는 넣지 않는다."""
    rule = FORMAT_RULES[q["format"]].replace("{n}", str(q.get("select_count") or 2))
    docs = "\n\n".join(f'<document page="{p}">\n{text}\n</document>' for p, text in snapshots.items())
    return prompts.render("crosscheck", format_rule=rule, question=_question_text(q), documents=docs)


_LABEL = re.compile(r"^\(?([A-Za-z])(?:[\).:\s]|$)")


def _choice_ids(answer: str) -> list[str]:
    out = []
    for a in answer.split(","):
        a = str(a).strip()
        m = _LABEL.match(a)
        out.append(m.group(1).upper() if m else a.upper())
    return sorted(set(out))


def verdict(q: dict, result: dict) -> str:
    """match | mismatch | unanswerable | error. 답이 비었는데 unanswerable이 아니면 error다."""
    if result.get("error"):
        return "error"
    if result.get("unanswerable"):
        return "unanswerable"
    answer = str(result.get("answer") or "").strip()
    if not answer:
        return "error"
    fmt = q["format"]
    submitted = [answer] if fmt == "short" else _choice_ids(answer)
    return "match" if grading.grade(fmt, submitted, q) else "mismatch"


def flags(verdicts: dict[str, str]) -> dict:
    """두 모델 모두 정답 키와 다르면 1순위, 하나만 다르면 2순위. 모두 unanswerable이면 근거 약함 신호."""
    values = list(verdicts.values())
    mismatches = values.count("mismatch")
    priority = 1 if values and mismatches == len(values) else 2 if mismatches else None
    flagged = mismatches > 0 or "unanswerable" in values
    weak = bool(values) and all(v == "unanswerable" for v in values)
    return {"priority": priority, "flagged": flagged, "weak_grounding": weak}


def ask(model, prompt: str) -> dict:
    try:
        out = model.with_structured_output(CrossAnswer, include_raw=True).invoke(prompt)
    except Exception as e:  # 한 모델 실패로 점검 전체를 멈추지 않는다
        return {"error": f"{type(e).__name__}: {e}"}
    if out.get("parsed") is None:
        return {"error": f"schema_invalid: {out.get('parsing_error')}"}
    return out["parsed"].model_dump()


def check_question(q: dict, snapshots: dict[str, str], models: dict) -> dict:
    prompt = build_prompt(q, snapshots)
    results = {}
    for name, model in models.items():
        r = ask(model, prompt)
        results[name] = {**r, "verdict": verdict(q, r)}
    item = {
        "question_id": q["question_id"], "format": q["format"],
        "answer_key": q["answer_key"], "accepted_answers": q.get("accepted_answers"),
        "results": results,
    }
    return item | flags({k: v["verdict"] for k, v in results.items()}) | {"reviewed": None}


def load_targets(conn, pool_id: str | None = None, batch_id: str | None = None,
                 include_code: bool = False) -> list[dict]:
    if (pool_id is None) == (batch_id is None):
        raise ValueError("give exactly one of pool_id, batch_id")
    if pool_id is not None:
        rows = conn.execute(
            """SELECT q.* FROM questions q JOIN pool_snapshot_items i ON i.question_id = q.question_id
               WHERE i.pool_snapshot_id = ? AND q.status = 'passed' ORDER BY q.question_id""", (pool_id,))
    else:
        rows = conn.execute("SELECT * FROM questions WHERE batch_id = ? AND status = 'passed' ORDER BY question_id",
                            (batch_id,))
    out = []
    for r in rows.fetchall():
        if r["format"] in SKIP_FORMATS and not include_code:
            continue
        pages = [p[0] for p in conn.execute(
            "SELECT page FROM grounding_records WHERE question_id = ? ORDER BY idx", (r["question_id"],))]
        out.append({
            "question_id": r["question_id"], "format": r["format"], "stem_en": r["stem_en"],
            "choices": json.loads(r["choices_json"]) if r["choices_json"] else None,
            "select_count": r["select_count"],
            "answer_key": json.loads(r["answer_key_json"]),
            "accepted_answers": json.loads(r["accepted_answers_json"]) if r["accepted_answers_json"] else None,
            "pages": list(dict.fromkeys(pages)),
        })
    return out


def read_snapshots(pages: list[str]) -> dict[str, str]:
    by_path = {r["path"]: r for r in allowlist.load_rows()}
    return {p: allowlist.read_snapshot(by_path[p]) for p in pages}


def _previous_reviews(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {i["question_id"]: i.get("reviewed") for i in data.get("items", []) if i.get("reviewed")}


def summary_table(items: list[dict], names: tuple[str, ...]) -> str:
    head = "| 문항 | 형식 | 정답 키 | " + " | ".join(names) + " | 순위 | 근거 약함 | 검토 |"
    lines = [head, "| " + " | ".join(["---"] * (len(names) + 6)) + " |"]
    for i in items:
        if not i["flagged"] and not any(r["verdict"] == "error" for r in i["results"].values()):
            continue
        cells = [f"{r['verdict']} {r.get('answer') or ''}".strip() for r in (i["results"][n] for n in names)]
        lines.append(f"| {i['question_id']} | {i['format']} | {i['answer_key']} | " + " | ".join(cells)
                     + f" | {i['priority'] or '-'} | {'예' if i['weak_grounding'] else '-'} | {i['reviewed'] or '-'} |")
    return "\n".join(lines)


def run(pool_id: str | None = None, batch_id: str | None = None, include_code: bool = False,
        models: dict | None = None, workers: int = WORKERS) -> Path:
    if models is None:
        check_region()
        models = {m: llm.chat_model(m, temperature=0) for m in MODELS}
    with db.connect() as conn:
        targets = load_targets(conn, pool_id=pool_id, batch_id=batch_id, include_code=include_code)
    target_id = pool_id or batch_id
    path = OUT_DIR / f"{target_id}.json"
    reviews = _previous_reviews(path)

    def one(q):
        item = check_question(q, read_snapshots(q["pages"]), models)
        item["reviewed"] = reviews.get(q["question_id"])
        return item

    with ThreadPoolExecutor(max_workers=workers) as ex:
        items = list(ex.map(one, targets))
    names = tuple(models)
    data = {
        "target": target_id, "kind": "pool" if pool_id else "batch", "models": list(names),
        "created_at": store.now(), "review_values": list(REVIEW_VALUES),
        "summary": {
            "questions": len(items),
            "flagged": [i["question_id"] for i in items if i["flagged"]],
            "priority_1": [i["question_id"] for i in items if i["priority"] == 1],
            "priority_2": [i["question_id"] for i in items if i["priority"] == 2],
            "weak_grounding": [i["question_id"] for i in items if i["weak_grounding"]],
            "errors": [i["question_id"] for i in items if any(r["verdict"] == "error" for r in i["results"].values())],
        },
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    path.with_suffix(".md").write_text(
        f"# crosscheck {target_id}\n\n{summary_table(items, names)}\n", encoding="utf-8")
    return path
