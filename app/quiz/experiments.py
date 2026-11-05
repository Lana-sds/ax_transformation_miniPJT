"""04 프롬프트·모델 실험 하네스(04 계획 1단계 1-가, 결정 5, 6). design.md 4.1과 인터페이스 장에 없는 요소다.

- arm 하나 = 프롬프트 디렉토리(`QUIZ_PROMPTS_DIR`) × 모델. 결과는 `data/experiments/<EXP-n>/`에 둔다.
- EXP-1 `run_judge`: 생성 없이 Judge 노드(`nodes.judge`)만 문항마다 한 번 돌린다. 문항은 `data/quiz.db`
  (`QUIZ_DB`)를 읽기 전용으로 열어 읽거나 문항 파일에 인라인으로 준다. 결과는 `<arm>.json`이다.
  DB에는 쓰지 않는다. 오류 없이 끝난 문항은 다시 돌리지 않는다(재개).
- EXP-2: `quiz generate --slots <json>`으로 arm마다 실험 DB(`QUIZ_DB=data/experiments/EXP-2/<arm>.db`)에
  생성한다. `data/quiz.db`를 가리키면 멈춘다(`require_experiment_db`).
- `summary`: EXP-1은 arm JSON, EXP-2는 arm DB를 읽어 표를 만든다. EXP-2는 `metrics.build`를 다시 쓴다.

문항 파일(`--items`) 모양. 목록 또는 `{"items": [...]}`:

    {"item_id": "real-001",            # 파일 안에서 유일
     "source": "db" | "inline",
     "question_id": "b...-001",        # db면 필수. inline이면 선택(근거 페이지를 그 문제 슬롯에서 찾는다)
     "question": {...},                # inline이면 필수. 파이프라인 문제 모양(`format` 포함)
     "slot": {"bucket", "topic", "format", "question_type"},  # 선택. 근거 페이지를 이 슬롯에서 찾는다
     "pages": ["/oss/..."],            # 선택. 주면 이 페이지 스냅샷을 Judge에게 준다
     "label": {...}}                   # 선택. Judge에게 보이지 않고 결과에 그대로 옮긴다

`summary`가 읽는 라벨 키: `defect_type`(결함 유형, 정상 문항은 null), `origin`(real | injected, 기본 real),
`subset`(정상 문항의 부분집합: audit_clean | crosscheck_clean).

Judge에게 주는 근거 페이지: `pages` > 슬롯 페이지(`slot` 또는 DB 문제의 버킷·주제·형식·유형으로
`slots.slot_for`, 파이프라인 judge 노드가 본 것과 같다) > 인용 페이지 순이다.
"""

import hashlib
import json
import re
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import ValidationError

from quiz import allowlist, db, llm, metrics, store
from quiz import slots as slot_plan
from quiz.pipeline import nodes, prompts
from quiz.pipeline.schemas import SCHEMAS

EXP_DIR = db.DATA_DIR / "experiments"
DEFAULT_DB = db.DATA_DIR / "quiz.db"
JUDGE_EXP = "EXP-1"
WORKERS = 2
SOURCES = ("db", "inline")
SLOT_KEYS = ("bucket", "topic", "format", "question_type")
_ARM_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

RESULT_KEYS = ("item_id", "source", "question_id", "format", "pages", "label", "verdict", "fail_reasons",
               "rejected", "input_tokens", "output_tokens", "cost_usd", "latency_s", "error", "judged_at")

EXP1_COLUMNS = {
    "detection": ("arm", "origin", "defect_type", "detected", "total", "rate"),
    "false_reject": ("arm", "subset", "rejected", "total", "rate"),
    "cost": ("arm", "calls", "errors", "input_tokens_per_call", "output_tokens_per_call", "cost_usd_per_call",
             "latency_s_per_call", "cost_usd_total"),
    "flips": ("arm_a", "arm_b", "compared", "flips", "flipped_items"),
}
EXP2_COLUMNS = ("arm", "slots", "passed", "first_quote_match", "first_attempts", "first_quote_match_rate",
                "retry_quote_pass", "retries_after_quote_mismatch", "retry_quote_pass_rate", "judge_pass_rate",
                "t2_11_fails", "drops", "cost_usd", "cost_per_passed", "seconds")
# 출제 품질(T2.11) Judge 항목 실패 이유
T2_11_REASONS = tuple(f"judge_fail:{i}" for i in nodes.CHOICE_JUDGE_ITEMS)
ALL = "(all)"


class ExperimentError(RuntimeError):
    pass


# --- DB ---

def is_default_db(path: Path | None = None) -> bool:
    return Path(path or db.db_path()).resolve() == DEFAULT_DB.resolve()


def require_experiment_db() -> None:
    """실험 생성은 `data/quiz.db`에 쓰지 않는다. `QUIZ_DB`가 실험 DB를 가리켜야 한다."""
    if is_default_db():
        raise ExperimentError(
            f"experiment run would write to {DEFAULT_DB}. Set QUIZ_DB to data/experiments/<EXP-n>/<arm>.db")


def connect_ro(path: Path) -> sqlite3.Connection:
    """읽기 전용 연결(`mode=ro` URI). 쓰기는 sqlite3.OperationalError가 난다."""
    path = Path(path)
    if not path.exists():
        raise ExperimentError(f"database not found: {path}")
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# --- 고정 슬롯(EXP-2) ---

def load_slots(path: Path, rows: list[dict] | None = None) -> list[dict]:
    """고정 슬롯 파일을 읽는다. 목록 또는 `{"slots": [...]}`이고 슬롯은 `slots.plan_slots` 출력 모양이다.

    슬롯마다 허용 목록에서 `slots.slot_for`로 다시 만든다(재개와 같다). 파일에 `pages`가 있으면 다시 만든
    페이지와 같아야 한다. 허용 목록이 바뀌어 arm마다 근거가 달라지는 것을 막는다.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = data.get("slots") if isinstance(data, dict) else data
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"{path}: needs a non-empty slot list")
    rows = rows if rows is not None else allowlist.load_rows()
    out = []
    for no, s in enumerate(entries, start=1):
        missing = [k for k in SLOT_KEYS if not (isinstance(s, dict) and s.get(k))]
        if missing:
            raise ValueError(f"{path}: slot {no} misses {missing}")
        full = slot_plan.slot_for(rows, s["bucket"], s["topic"], s["format"], s["question_type"])
        if "pages" in s and list(s["pages"]) != full["pages"]:
            raise ValueError(f"{path}: slot {no} pages differ from the allowlist: {s['pages']} != {full['pages']}")
        out.append(full)
    return out


# --- 문항 파일(EXP-1) ---

def load_items(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise ExperimentError(f"{path}: needs a non-empty item list")
    seen = set()
    for no, it in enumerate(items, start=1):
        where = f"{path}: item {no}"
        if not isinstance(it, dict):
            raise ExperimentError(f"{where}: not an object")
        iid = it.get("item_id")
        if not isinstance(iid, str) or not iid or iid in seen:
            raise ExperimentError(f"{where}: item_id missing or repeated: {iid!r}")
        seen.add(iid)
        if it.get("source") not in SOURCES:
            raise ExperimentError(f"{where}: source must be one of {SOURCES}")
        if it["source"] == "db" and not isinstance(it.get("question_id"), str):
            raise ExperimentError(f"{where}: source db needs question_id")
        if it["source"] == "inline":
            q = it.get("question")
            if not isinstance(q, dict) or q.get("format") not in nodes.ALL_FORMATS:
                raise ExperimentError(f"{where}: source inline needs question with format in {nodes.ALL_FORMATS}")
        if "slot" in it and not (isinstance(it["slot"], dict) and all(it["slot"].get(k) for k in SLOT_KEYS)):
            raise ExperimentError(f"{where}: slot needs {SLOT_KEYS}")
        if "pages" in it and not (isinstance(it["pages"], list) and it["pages"]):
            raise ExperimentError(f"{where}: pages must be a non-empty list")
        if not isinstance(it.get("label", {}), dict):
            raise ExperimentError(f"{where}: label must be an object")
    return items


def _normalize(question: dict) -> dict:
    """파이프라인 generate 노드 출력과 같은 키 순서로 맞춘다(Judge가 보는 JSON이 같게). 스키마에 안 맞는
    결함 주입 사본은 그대로 둔다."""
    fmt = question["format"]
    body = {k: v for k, v in question.items() if k != "format"}
    try:
        out = SCHEMAS[fmt].model_validate(body).model_dump()
    except ValidationError:
        out = body
    out["format"] = fmt
    return out


def question_from_row(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    recs = [{"page": r["page"], "quote": r["quote"], "answer_basis": r["answer_basis"]} for r in conn.execute(
        "SELECT page, quote, answer_basis FROM grounding_records WHERE question_id = ? ORDER BY idx",
        (row["question_id"],))]
    q = {"stem_en": row["stem_en"], "explanation_ko": row["explanation_ko"],
         "segments": json.loads(row["segments_json"]), "grounding_records": recs, "cca_f_tag": row["cca_f_tag"]}
    if row["choices_json"]:
        q["choices"] = json.loads(row["choices_json"])
    q["answer_key"] = json.loads(row["answer_key_json"])
    if row["select_count"] is not None:
        q["select_count"] = row["select_count"]
    if row["accepted_answers_json"]:
        q["accepted_answers"] = json.loads(row["accepted_answers_json"])
    if row["exec_spec_json"]:
        q["exec_spec"] = json.loads(row["exec_spec_json"])
    q["format"] = row["format"]
    return _normalize(q)


def _pages(item: dict, question: dict, row, rows: list[dict]) -> list[str]:
    if item.get("pages"):
        return list(item["pages"])
    slot = item.get("slot") or (
        {k: row[k] for k in SLOT_KEYS} if row is not None else None)
    if slot:
        try:
            return slot_plan.slot_for(rows, slot["bucket"], slot["topic"], slot["format"],
                                      slot["question_type"])["pages"]
        except ValueError:
            pass
    return list(dict.fromkeys(r["page"] for r in question.get("grounding_records") or []))


def _prepare(items: list[dict], rows: list[dict]) -> dict[str, dict]:
    """문항마다 Judge 입력(문제, 근거 페이지)을 만든다. DB는 읽기 전용으로 한 번만 연다."""
    by_path = {r["path"]: r for r in rows}
    conn = connect_ro(db.db_path()) if any(it.get("question_id") for it in items) else None
    out = {}
    try:
        for it in items:
            base = {"item_id": it["item_id"], "source": it["source"], "question_id": it.get("question_id"),
                    "label": it.get("label", {})}
            try:
                row = None
                if it.get("question_id"):
                    row = conn.execute("SELECT * FROM questions WHERE question_id = ?",
                                       (it["question_id"],)).fetchone()
                    if row is None and it["source"] == "db":
                        raise ExperimentError(f"question not in database: {it['question_id']}")
                question = question_from_row(conn, row) if it["source"] == "db" else _normalize(it["question"])
                pages = _pages(it, question, row, rows)
                unknown = [p for p in pages if p not in by_path]
                if not pages or unknown:
                    raise ExperimentError(f"pages not in allowlist: {unknown or pages}")
                out[it["item_id"]] = base | {"format": question["format"], "pages": pages, "question": question,
                                             "snapshots": {p: allowlist.read_snapshot(by_path[p]) for p in pages}}
            except (ExperimentError, KeyError, ValueError) as e:
                out[it["item_id"]] = base | {"format": None, "pages": [], "error": f"{type(e).__name__}: {e}"}
    finally:
        if conn is not None:
            conn.close()
    return out


def _empty_result(prep: dict) -> dict:
    return {k: prep.get(k) for k in ("item_id", "source", "question_id", "format", "pages", "label")} | {
        "verdict": None, "fail_reasons": [], "rejected": None, "input_tokens": 0, "output_tokens": 0,
        "cost_usd": None, "latency_s": None, "error": prep.get("error"), "judged_at": store.now()}


def judge_one(prep: dict, model) -> dict:
    """Judge 노드 1회. 파이프라인과 같은 프롬프트와 실패 이유 규칙을 쓴다(`nodes.judge`)."""
    result = _empty_result(prep)
    if prep.get("error"):
        return result
    state = {"slot": {"format": prep["format"]}, "snapshots": prep["snapshots"], "question": prep["question"],
             "fail_reasons": []}
    start = time.perf_counter()
    try:
        out = nodes.judge(state, model)
    except Exception as e:  # noqa: BLE001 - 한 문항 실패로 arm을 멈추지 않는다. 재개 때 다시 돈다
        return result | {"error": f"{type(e).__name__}: {e}", "latency_s": round(time.perf_counter() - start, 3)}
    tokens = out.get("tokens") or {}
    fails = out.get("fail_reasons") or []
    return result | {
        "verdict": out.get("judge"), "fail_reasons": fails, "rejected": bool(fails),
        "input_tokens": tokens.get("input", 0), "output_tokens": tokens.get("output", 0),
        "cost_usd": tokens.get("cost_usd"), "latency_s": round(time.perf_counter() - start, 3),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def arm_path(exp: str, arm: str) -> Path:
    if not _ARM_NAME.match(arm) or not _ARM_NAME.match(exp):
        raise ExperimentError(f"bad experiment or arm name: {exp!r} / {arm!r}")
    return EXP_DIR / exp / f"{arm}.json"


def _model_for(model_id: str):
    if model_id == llm.JUDGE_MODEL:
        return llm.judge_model()
    return llm.failover_chain((model_id,), temperature=0)


def run_judge(items_path: Path, arm: str, model_id: str | None = None, model=None, exp: str = JUDGE_EXP,
              workers: int = WORKERS) -> Path:
    """문항 파일의 문항마다 Judge를 돌려 `data/experiments/<exp>/<arm>.json`에 쓴다.

    같은 arm 파일이 있으면 오류 없이 끝난 문항은 두고 나머지만 돈다. 모델이나 프롬프트 디렉토리가
    다르면 멈춘다(다른 arm 이름을 쓴다).
    """
    items = load_items(items_path)
    rows = allowlist.load_rows()
    allowlist.verify(rows)
    model_id = model_id or llm.JUDGE_MODEL
    path = arm_path(exp, arm)
    meta = {
        "exp": exp, "arm": arm, "model": model_id, "prompts_dir": str(prompts.prompt_dir()),
        "extra_items": [i["name"] for i in nodes.extra_judge_items()],
        "allowlist_sha256": _sha256(allowlist.ALLOWLIST_PATH),
        "items_file": str(items_path), "items_sha256": _sha256(items_path),
    }
    done: dict[str, dict] = {}
    created_at = store.now()
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        for key in ("model", "prompts_dir", "extra_items"):
            if old.get(key) != meta[key]:
                raise ExperimentError(f"{path} was run with {key}={old.get(key)!r}, now {meta[key]!r}. "
                                      "Use another arm name")
        done = {r["item_id"]: r for r in old.get("results", []) if r.get("error") is None}
        created_at = old.get("created_at", created_at)

    prepared = _prepare(items, rows)
    todo = [it["item_id"] for it in items if it["item_id"] not in done]
    if model is None and todo:
        model = _model_for(model_id)
    lock = threading.Lock()

    def save() -> None:
        results = [done[it["item_id"]] for it in items if it["item_id"] in done]
        data = meta | {"created_at": created_at, "updated_at": store.now(), "results": results}
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    def one(item_id: str) -> None:
        result = judge_one(prepared[item_id], model)
        with lock:
            done[item_id] = result
            save()
        state = result["error"] or ("rejected " + ",".join(result["fail_reasons"]) if result["rejected"] else "pass")
        print(f"{item_id} {state}", flush=True)

    print(f"exp={exp} arm={arm} model={model_id} items={len(items)} to_judge={len(todo)}", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, todo))
    with lock:
        save()
    return path


# --- summary ---

def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def _mean(values: list) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def _arm_files(exp_dir: Path) -> dict[str, dict]:
    out = {}
    for p in sorted(exp_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "arm" in data and isinstance(data.get("results"), list):
            out[data["arm"]] = data
    return out


def _judged(data: dict) -> list[dict]:
    return [r for r in data["results"] if r.get("error") is None]


def _origin(r: dict) -> str:
    return (r.get("label") or {}).get("origin") or "real"


def _defect(r: dict) -> str | None:
    return (r.get("label") or {}).get("defect_type")


def _summary_judge(arms: dict[str, dict], compare: tuple[str, str] | None) -> list[dict]:
    detection, false_reject, cost = [], [], []
    for arm, data in arms.items():
        judged = _judged(data)
        for origin in ("real", "injected"):
            defects = [r for r in judged if _defect(r) and _origin(r) == origin]
            groups = sorted({_defect(r) for r in defects})
            for dt in groups + ([ALL] if defects else []):
                rs = defects if dt == ALL else [r for r in defects if _defect(r) == dt]
                hit = sum(1 for r in rs if r["rejected"])
                detection.append({"arm": arm, "origin": origin, "defect_type": dt, "detected": hit,
                                  "total": len(rs), "rate": _rate(hit, len(rs))})
        normal = [r for r in judged if not _defect(r)]
        subsets = sorted({(r.get("label") or {}).get("subset") or "unspecified" for r in normal})
        for sub in subsets + ([ALL] if normal else []):
            rs = normal if sub == ALL else [
                r for r in normal if ((r.get("label") or {}).get("subset") or "unspecified") == sub]
            rej = sum(1 for r in rs if r["rejected"])
            false_reject.append({"arm": arm, "subset": sub, "rejected": rej, "total": len(rs),
                                 "rate": _rate(rej, len(rs))})
        costs = [r["cost_usd"] for r in judged]
        known = None if any(c is None for c in costs) else costs
        cost.append({
            "arm": arm, "calls": len(judged), "errors": len(data["results"]) - len(judged),
            "input_tokens_per_call": _mean([r["input_tokens"] for r in judged]),
            "output_tokens_per_call": _mean([r["output_tokens"] for r in judged]),
            "cost_usd_per_call": _mean(known) if known is not None else None,
            "latency_s_per_call": _mean([r["latency_s"] for r in judged]),
            "cost_usd_total": round(sum(known), 6) if known else None,
        })
    tables = [
        {"name": "detection", "columns": list(EXP1_COLUMNS["detection"]), "rows": detection},
        {"name": "false_reject", "columns": list(EXP1_COLUMNS["false_reject"]), "rows": false_reject},
        {"name": "cost", "columns": list(EXP1_COLUMNS["cost"]), "rows": cost},
    ]
    if compare:
        a, b = compare
        missing = [x for x in (a, b) if x not in arms]
        if missing:
            raise ExperimentError(f"arm not found for --compare: {missing}")
        ra = {r["item_id"]: r["rejected"] for r in _judged(arms[a])}
        rb = {r["item_id"]: r["rejected"] for r in _judged(arms[b])}
        both = [i for i in ra if i in rb]
        flipped = [i for i in both if ra[i] != rb[i]]
        tables.append({"name": "flips", "columns": list(EXP1_COLUMNS["flips"]), "rows": [
            {"arm_a": a, "arm_b": b, "compared": len(both), "flips": len(flipped), "flipped_items": flipped}]})
    return tables


def _generate_row(arm: str, conn: sqlite3.Connection) -> dict:
    m = metrics.build(conn)
    slots_n = conn.execute("SELECT COUNT(*) FROM batch_slots").fetchone()[0]
    passed = conn.execute("SELECT COUNT(*) FROM questions WHERE status = 'passed'").fetchone()[0]
    first_n, first_ok = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(quote_match), 0) FROM verification_results"
        " WHERE attempt_no = 0 AND quote_match IS NOT NULL").fetchone()
    attempts = {(r["question_id"], r["attempt_no"]): r for r in conn.execute(
        "SELECT question_id, attempt_no, quote_match, fail_reasons_json FROM verification_results")}
    reasons = {k: json.loads(r["fail_reasons_json"] or "[]") for k, r in attempts.items()}
    # quote_mismatch 피드백 뒤 재시도: 직전 시도에 quote_mismatch가 있던 시도. 통과 = quote_match 1
    retries = [r for (qid, n), r in attempts.items()
               if n > 0 and "quote_mismatch" in reasons.get((qid, n - 1), []) and r["quote_match"] is not None]
    retry_ok = sum(1 for r in retries if r["quote_match"] == 1)
    t2_11 = sum(1 for rs in reasons.values() for x in rs if x in T2_11_REASONS)
    batches = m["batches"]
    costs = [b["cost_usd"] for b in batches]
    seconds = [b["seconds"] for b in batches]
    cost = round(sum(costs), 6) if costs and None not in costs else None
    return {
        "arm": arm, "slots": slots_n, "passed": passed,
        "first_quote_match": first_ok, "first_attempts": first_n, "first_quote_match_rate": _rate(first_ok, first_n),
        "retry_quote_pass": retry_ok, "retries_after_quote_mismatch": len(retries),
        "retry_quote_pass_rate": _rate(retry_ok, len(retries)),
        "judge_pass_rate": m["judge_pass_rate"]["rate"], "t2_11_fails": t2_11,
        "drops": m["drops"]["by_reason"], "cost_usd": cost,
        "cost_per_passed": round(cost / passed, 6) if cost is not None and passed else None,
        "seconds": sum(seconds) if seconds and None not in seconds else None,
    }


def _summary_generate(dbs: list[Path]) -> list[dict]:
    rows = []
    for p in dbs:
        conn = connect_ro(p)
        try:
            rows.append(_generate_row(p.stem, conn))
        finally:
            conn.close()
    return [{"name": "arms", "columns": list(EXP2_COLUMNS), "rows": rows}]


def summary(exp: str, compare: tuple[str, str] | None = None) -> dict:
    """arm JSON(EXP-1 모양)과 arm DB(EXP-2 모양)를 찾아 표를 만든다."""
    exp_dir = EXP_DIR / exp
    if not exp_dir.is_dir():
        raise ExperimentError(f"experiment directory not found: {exp_dir}")
    arms = _arm_files(exp_dir)
    dbs = sorted(exp_dir.glob("*.db"))
    if not arms and not dbs:
        raise ExperimentError(f"no arm results in {exp_dir} (<arm>.json or <arm>.db)")
    tables = (_summary_judge(arms, compare) if arms else []) + (_summary_generate(dbs) if dbs else [])
    return {"exp": exp, "tables": tables}


def _cell(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, dict):
        return ", ".join(f"{k}:{n}" for k, n in v.items()) or "-"
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "-"
    return str(v)


def render(s: dict) -> str:
    parts = [f"# {s['exp']} summary"]
    for t in s["tables"]:
        lines = [f"## {t['name']}", "", "| " + " | ".join(t["columns"]) + " |",
                 "| " + " | ".join(["---"] * len(t["columns"])) + " |"]
        lines += ["| " + " | ".join(_cell(r.get(c)) for c in t["columns"]) + " |" for r in t["rows"]]
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"
