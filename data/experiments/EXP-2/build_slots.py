"""EXP-2 고정 슬롯 12개를 만든다(계획 1-나 7번).

버킷마다 2슬롯, 형식 4종이 3개씩이다. 시드로 형식 짝 배정, 주제, 유형을 고른다.
arena 과제 정의(`arena/task.md`)에 실패 예시로 보인 페이지를 쓰는 주제는 뺀다.

실행: `cd app && uv run python ../data/experiments/EXP-2/build_slots.py`
"""

import json
import random
from pathlib import Path

from quiz import slots as S

SEED = 20261105
OUT = Path(__file__).with_name("slots.json")
# 05-m4.md 7·8회차 실패 예시 페이지. 변형 작성자에게 보였다
EXCLUDE_PAGE_PARTS = ("langsmith/studio", "graph-api-control-flow")
PAIRS = [("single", "multi"), ("short", "code")] * 3


def allowed_types(t: dict, fmt: str) -> list[str]:
    if fmt == S.CODE_FORMAT:
        return S.TYPES_CODE
    if t["is_mcp"]:
        return S.TYPES_MCP
    if fmt == "short":
        return S.TYPES_SHORT
    return S.TYPES_OTHER


def main() -> None:
    rng = random.Random(SEED)
    topics = [t for t in S.group_topics(S.load_allowlist_md())
              if t["status"] != S.MISSING
              and not any(part in p for p in t["pages"] for part in EXCLUDE_PAGE_PARTS)]
    pairs = PAIRS[:]
    rng.shuffle(pairs)
    out = []
    for bucket, pair in zip(S.BUCKETS, pairs):
        cands = [t for t in topics if t["bucket"] == bucket]
        used: set[str] = set()
        for fmt in pair:
            pool = [t for t in cands if t["topic"] not in used and (fmt != S.CODE_FORMAT or S._code_ok(t))]
            t = rng.choice(pool)
            used.add(t["topic"])
            slot = S._slot(t, fmt, rng.choice(allowed_types(t, fmt)))
            out.append(slot)
    meta = {"seed": SEED, "exclude_page_parts": list(EXCLUDE_PAGE_PARTS), "slots": out}
    OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for s in out:
        print(s["bucket"], s["format"], s["question_type"], s["topic"], s["pages"])


if __name__ == "__main__":
    main()
