"""EXP-1 문항 목록 `items.json`을 만든다(계획 1-나 2~6번).

- 실제 결함 18, `audit_clean` 3: 사용자가 2026-11-05에 확인한 라벨이다(01-harness.md).
- `crosscheck_clean`: 현재 풀 중 감사 표본이 아니고, 교차 풀이에서 걸리지 않았고, 두 모델 모두 정답 키와
  일치한 문항. `03-045`, `03-048`은 뺀다.
- 결함 주입 24: `crosscheck_clean` 문항 사본에 결함 하나씩. 라벨은 구성으로 정해진다.

`data/quiz.db`는 읽기 전용으로 연다. 실행: `cd app && uv run python ../data/experiments/EXP-1/build_items.py`
"""

import copy
import json
import random
import re
import sqlite3
from pathlib import Path

from quiz import db, experiments, snapshots

SEED = 20261105
OUT = Path(__file__).with_name("items.json")
POOL = "ps_326384fb5422"
CROSSCHECK = ["ps_5dac983c4b29", "b20261105-14", "b20261105-15"]
P = "b20261105-"

REAL = [  # (문항, 유형, 기대 항목)
    ("03-010", "key_error", ["answer_key_correct"]),
    ("03-008", "quote_irrelevant", ["quote_supports_answer"]),
    ("03-009", "explanation_error", ["explanation_correct"]),
    ("03-021", "explanation_error", ["explanation_correct"]),
    ("03-013", "explanation_error", ["explanation_correct"]),
    ("01-002", "explanation_error", ["explanation_correct"]),
    ("03-040", "cue", ["no_cue"]),
    ("05-007", "cue", ["no_cue"]),
    ("04-017", "cue", ["no_cue"]),
    ("01-001", "cue", ["no_cue"]),
    ("03-044", "cue", ["no_cue"]),
    ("03-033", "quote_irrelevant", ["quote_supports_answer"]),
    ("05-001", "quote_irrelevant", ["quote_supports_answer"]),
    ("03-059", "ambiguous", ["answer_key_correct", "distractors_wrong"]),
    ("03-056", "ambiguous", ["answer_key_correct"]),
    ("04-009", "ambiguous", ["answer_key_correct", "explanation_correct"]),
    ("03-060", "ambiguous", ["answer_key_correct"]),
    ("03-023", "mapping", ["mapping_faithful"]),
]
AUDIT_CLEAN = ["03-039", "02-004", "04-012"]
EXCLUDE = {P + "03-045", P + "03-048"}

INJECT = {  # 유형: (원본 형식, 개수, 기대 항목)
    "key_error": (("single", "multi"), 6, ["answer_key_correct"]),
    "explanation_error": (("single", "multi"), 6, ["explanation_correct"]),
    "cue": (("single", "multi"), 6, ["no_cue"]),
    "quote_irrelevant": (("short",), 6, ["quote_supports_answer"]),
}
PAD = [" This follows from how the framework handles this exact situation, as the reference describes.",
       " It also matches the documented default behavior for this configuration in the current version.",
       " In practice this is the outcome a developer observes when running the code as written."]
# 해설 문단 머리 예: "**A (정답):**", "**B (오답)**:", "A. 정답입니다.", "A: ...", "A) ...", "A선택지: ..."
HEAD = re.compile(r"^(?:\*\*\s*)?(?:선택지\s*)?([A-E])(?:\s*선택지)?(?:\s*\([^)]*\))?(?:\s*\*\*)?\s*[.:)]\s*(?:\*\*)?\s*"
                  r"|^\*\*\s*(?:선택지\s*)?([A-E])\b[^*]*\*\*\s*:?\s*")


def crosscheck_clean(conn) -> list[str]:
    pool = {r[0] for r in conn.execute("SELECT question_id FROM pool_snapshot_items WHERE pool_snapshot_id = ?",
                                       (POOL,))}
    audit = {r[0] for r in conn.execute("SELECT question_id FROM audit_records")}
    items = {}
    for name in CROSSCHECK:
        for it in json.loads((db.DATA_DIR / "crosscheck" / f"{name}.json").read_text(encoding="utf-8"))["items"]:
            items[it["question_id"]] = it
    return sorted(q for q, it in items.items()
                  if q in pool and q not in audit and q not in EXCLUDE and not it["flagged"]
                  and all(r["verdict"] == "match" for r in it["results"].values()))


def words(text: str) -> int:
    return len(text.split())


def split_expl(text: str) -> list[tuple[str | None, str, str]] | None:
    """해설을 (보기 id, 머리, 본문) 문단으로 나눈다. 보기 머리가 없는 문단이 있으면 None."""
    out = []
    for para in [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]:
        m = HEAD.match(para)
        if not m:
            return None
        out.append((m.group(1) or m.group(2), para[:m.end()], para[m.end():]))
    return out


def inject_key(q: dict, rng: random.Random) -> str:
    ids = [c["id"] for c in q["choices"]]
    key = list(q["answer_key"])
    wrong = [i for i in ids if i not in key]
    old, new = rng.choice(key), rng.choice(wrong)
    q["answer_key"] = sorted([k for k in key if k != old] + [new])
    return f"정답 키 {old}를 오답 {new}로 바꿨다: {key} -> {q['answer_key']}"


def inject_expl(q: dict, rng: random.Random) -> str | None:
    paras = split_expl(q["explanation_ko"])
    ids = [c["id"] for c in q["choices"]]
    if not paras or sorted(p[0] for p in paras) != sorted(ids):
        return None
    wrong = [i for i, p in enumerate(paras) if p[0] not in q["answer_key"]]
    target = rng.choice(wrong)
    donor = rng.choice([i for i in range(len(paras)) if i != target])
    paras[target] = (paras[target][0], paras[target][1], paras[donor][2])
    q["explanation_ko"] = "\n\n".join(h + b for _, h, b in paras)
    return f"보기 {paras[target][0]} 해설 본문을 보기 {paras[donor][0]} 해설 본문으로 바꿨다"


def inject_cue(q: dict, rng: random.Random) -> str:
    key = set(q["answer_key"])
    for c in q["choices"]:
        if c["id"] not in key:
            c["text"] = c["text"].rstrip() + " This always happens."
    longest = max(words(c["text"]) for c in q["choices"] if c["id"] not in key)
    for c in q["choices"]:
        if c["id"] in key:
            pads = PAD[:]
            rng.shuffle(pads)
            while words(c["text"]) <= 1.6 * longest and pads:
                c["text"] = c["text"].rstrip() + pads.pop()
    return "오답마다 ' This always happens.'를 붙이고, 정답 보기를 가장 긴 오답의 1.6배 넘게 늘렸다"


def snapshot_text(page: str) -> str:
    name = snapshots.ref_snapshot_name(page) if page.startswith("http") else snapshots.snapshot_name(page)
    return (snapshots.SNAPSHOT_DIR / name).read_bytes().decode("utf-8")


def inject_quote(q: dict, rng: random.Random) -> str | None:
    answers = {a.lower() for a in (q.get("accepted_answers") or []) + list(q["answer_key"])}
    notes = []
    for rec in q["grounding_records"]:
        text = snapshot_text(rec["page"])
        at = text.find(rec["quote"][:40])
        cands = []
        for m in re.finditer(r"[^\n]{40,220}", text):
            s = m.group(0).strip()
            if (re.match(r"^[A-Z][^`\[\]|<>{}#*]*[.]$", s) and 40 <= len(s) <= 220
                    and (at < 0 or abs(m.start() - at) > 1500)
                    and not any(a in s.lower() for a in answers)
                    and s not in [r["quote"] for r in q["grounding_records"]]):
                cands.append(s)
        if not cands:
            return None
        rec["quote"] = rng.choice(cands)
        notes.append(rec["quote"][:60])
    return "인용을 모두 같은 페이지의 무관한 평문 문장으로 바꿨다: " + " / ".join(notes)


def main() -> None:
    rng = random.Random(SEED)
    conn = sqlite3.connect(f"file:{db.DATA_DIR / 'quiz.db'}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    row = {r["question_id"]: r for r in conn.execute("SELECT * FROM questions")}
    items = []
    for qid, dtype, expected in REAL:
        items.append({"item_id": f"real-{qid}", "source": "db", "question_id": P + qid,
                      "label": {"origin": "real", "defect_type": dtype, "expected_items": expected}})
    for qid in AUDIT_CLEAN:
        items.append({"item_id": f"norm-{qid}", "source": "db", "question_id": P + qid,
                      "label": {"origin": "real", "defect_type": None, "subset": "audit_clean"}})
    clean = crosscheck_clean(conn)
    for qid in clean:
        items.append({"item_id": f"norm-{qid[len(P):]}", "source": "db", "question_id": qid,
                      "label": {"origin": "real", "defect_type": None, "subset": "crosscheck_clean"}})

    used: set[str] = set()
    funcs = {"key_error": inject_key, "explanation_error": inject_expl, "cue": inject_cue,
             "quote_irrelevant": inject_quote}
    for dtype in ("explanation_error", "quote_irrelevant", "key_error", "cue"):  # 조건이 까다로운 것부터
        fmts, n, expected = INJECT[dtype]
        srcs = [q for q in clean if row[q]["format"] in fmts and q not in used]
        rng.shuffle(srcs)
        made = 0
        for qid in srcs:
            if made == n:
                break
            q = copy.deepcopy(experiments.question_from_row(conn, row[qid]))
            note = funcs[dtype](q, rng)
            if note is None:
                continue
            used.add(qid)
            made += 1
            r = row[qid]
            items.append({"item_id": f"inj-{dtype}-{qid[len(P):]}", "source": "inline", "question_id": qid,
                          "question": q, "slot": {k: r[k] for k in experiments.SLOT_KEYS},
                          "label": {"origin": "injected", "defect_type": dtype, "expected_items": expected,
                                    "source_question_id": qid, "injection": note}})
        if made < n:
            raise SystemExit(f"{dtype}: only {made}/{n} sources")
    OUT.write_text(json.dumps({"seed": SEED, "items": items}, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(len(items), "items")
    for it in items:
        if it["source"] == "inline":
            print(it["item_id"], "|", it["label"]["injection"][:110])


if __name__ == "__main__":
    main()
