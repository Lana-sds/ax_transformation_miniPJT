"""슬롯 계획(design.md 6.1 "슬롯 계획", US-2.4).

입력은 허용 목록 행(dict)이다. 키: `bucket`, `topic_no`(없으면 처음 나온 순서), `topic`, `path`, `kind`,
`status`(확인 | 근접 | 없음), 선택 키 `is_mcp`. `allowlist.yaml` 행과 같은 모양이라 그대로 넘길 수 있다.
`load_allowlist_md()`는 page-allowlist.md 표에서 같은 모양의 행을 만든다.

규칙
- 주제 상태: 행 중 하나라도 `확인`이면 확인, 아니면 하나라도 `근접`이면 근접, 아니면 없음.
  page-allowlist.md 요약 표(확인 30, 근접만 3, 없음 1)와 같은 규칙이다.
- `없음` 주제에는 슬롯을 배정하지 않는다(출제하지 않음, CR-9).
- 형식은 전체 슬롯 순서(버킷 순)에 따라 single, multi, short, code를 돌린다. 버킷당 10개면 버킷마다
  형식이 2~3개씩, 전체로 형식마다 15개가 된다. 버킷당 1개(pilot)면 6개 슬롯에 4형식이 모두 나온다.
- code 형식은 MCP 주제와 `없음` 주제에 배정하지 않는다(D-9). 섞인 주제(장애 주입)는 code 슬롯의
  `pages`에서 MCP 행을 뺀다.
- MCP 행은 경로에 `mcp`가 들어 있는 행이다. page-allowlist.md Tool · MCP 노트의 "#4, #5, #6의 `mcp/tools`"와
  같다. 주제의 모든 행이 MCP일 때 그 주제를 MCP 주제로 본다(#4, #5).
- 주제 배정: 버킷 안에서 code 슬롯을 먼저, 그다음 나머지를 순서대로, 사용 횟수가 가장 적은 주제에 준다.
  동률이면 그 주제에 같은 형식이 적은 쪽, 그다음 주제 번호 순이다.
- 유형: code는 code_behavior, error_cause를 번갈아, MCP 주제는 concept, design을 번갈아,
  단답은 concept, error_cause, design을, 그 밖은 concept, design, error_cause, code_behavior를 돌린다
  (버킷 안 순서 기준). 단답 답은 이름·용어로 제한하므로(D-3) 단답에는 code_behavior를 두지 않는다.
- `근접` 주제 슬롯은 `near=True`다. 생성 프롬프트에 "문서가 그 이름으로 패턴을 정의한다고 쓰지 말 것"을 넣는다.
  주제가 확인이어도 근접 행을 근거로 쓸 수 있으므로 `near_pages`에 그 행 경로를 둔다.
"""

import re
from pathlib import Path

from quiz.db import REPO_ROOT

ALLOWLIST_MD = REPO_ROOT / "docs" / "02-spec-design" / "output" / "page-allowlist.md"

BUCKETS = ["rag", "langgraph_basics", "tool_mcp", "middleware_hitl_guardrails", "multi_agent", "ops_quality"]
DAY_TO_BUCKET = {f"day{i}": b for i, b in enumerate(BUCKETS, start=2)}
FORMATS = ["single", "multi", "short", "code"]
CODE_FORMAT = "code"

TYPES_CODE = ["code_behavior", "error_cause"]
TYPES_MCP = ["concept", "design"]
TYPES_SHORT = ["concept", "error_cause", "design"]  # 단답은 이름·용어만 답하므로 code_behavior를 쓰지 않는다
TYPES_OTHER = ["concept", "design", "error_cause", "code_behavior"]

CONFIRMED, NEAR, MISSING = "확인", "근접", "없음"


def load_allowlist_md(path: Path = ALLOWLIST_MD) -> list[dict]:
    """page-allowlist.md의 dayN 절 표를 행 목록으로 읽는다."""
    rows: list[dict] = []
    bucket = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            m = re.search(r"\((day\d)\)", line)
            bucket = DAY_TO_BUCKET.get(m.group(1)) if m else None
            continue
        if bucket is None or not re.match(r"\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        no, topic, page, kind, status = cells[:5]
        page = page.strip("`")
        rows.append({
            "bucket": bucket,
            "topic_no": int(no),
            "topic": topic,
            "path": None if page in ("", "-") else page,
            "kind": None if kind in ("", "-") else kind,
            "status": status,
        })
    return rows


def is_mcp_row(row: dict) -> bool:
    if "is_mcp" in row:
        return bool(row["is_mcp"])
    return "mcp" in (row.get("path") or "").lower()


def _bucket_key(bucket: str, first_seen: dict[str, int]) -> tuple[int, int]:
    if bucket in BUCKETS:
        return (BUCKETS.index(bucket), 0)
    return (len(BUCKETS), first_seen[bucket])


def group_topics(rows: list[dict]) -> list[dict]:
    """행을 (버킷, 주제)로 묶는다. 버킷은 BUCKETS 순, 주제는 번호 순이다."""
    groups: dict[tuple[str, str], dict] = {}
    first_seen: dict[str, int] = {}
    for i, r in enumerate(rows):
        first_seen.setdefault(r["bucket"], i)
        key = (r["bucket"], r["topic"])
        g = groups.setdefault(key, {"bucket": r["bucket"], "topic": r["topic"], "topic_no": r.get("topic_no"),
                                    "order": i, "rows": []})
        g["rows"].append(r)

    topics = []
    for g in groups.values():
        statuses = {r["status"] for r in g["rows"]}
        status = CONFIRMED if CONFIRMED in statuses else NEAR if NEAR in statuses else MISSING
        page_rows = sorted((r for r in g["rows"] if r.get("path")), key=lambda r: r["path"])
        pages = list(dict.fromkeys(r["path"] for r in page_rows))
        mcp_pages = list(dict.fromkeys(r["path"] for r in page_rows if is_mcp_row(r)))
        near_pages = list(dict.fromkeys(r["path"] for r in page_rows if r["status"] == NEAR))
        topics.append({
            "bucket": g["bucket"],
            "topic_no": g["topic_no"],
            "topic": g["topic"],
            "status": status,
            "is_mcp": bool(g["rows"]) and all(is_mcp_row(r) for r in g["rows"]),
            "pages": pages,
            "mcp_pages": mcp_pages,
            "near_pages": near_pages,
            "_order": g["order"],
        })
    topics.sort(key=lambda t: (_bucket_key(t["bucket"], first_seen),
                               t["topic_no"] if t["topic_no"] is not None else t["_order"],
                               t["topic"]))
    for t in topics:
        del t["_order"]
    return topics


def _code_ok(topic: dict) -> bool:
    return topic["status"] != MISSING and not topic["is_mcp"] and bool(set(topic["pages"]) - set(topic["mcp_pages"]))


def _assign_topics(bucket: str, formats: list[str], topics: list[dict]) -> list[tuple[dict, str]]:
    usage = {id(t): 0 for t in topics}
    fmt_usage = {(id(t), f): 0 for t in topics for f in FORMATS}
    order = {id(t): i for i, t in enumerate(topics)}
    # code를 먼저 배정해야 code 가능 주제가 다른 형식으로 다 차지 않는다
    queue = [f for f in formats if f == CODE_FORMAT] + [f for f in formats if f != CODE_FORMAT]
    out = []
    for f in queue:
        cands = [t for t in topics if f != CODE_FORMAT or _code_ok(t)]
        if not cands:
            raise ValueError(f"bucket {bucket}: no topic can take format {f}")
        t = min(cands, key=lambda t: (usage[id(t)], fmt_usage[(id(t), f)], order[id(t)]))
        usage[id(t)] += 1
        fmt_usage[(id(t), f)] += 1
        out.append((t, f))
    out.sort(key=lambda tf: (order[id(tf[0])], FORMATS.index(tf[1]) if tf[1] in FORMATS else len(FORMATS)))
    return out


def plan_slots(rows: list[dict], per_bucket: int = 10, formats: list[str] = FORMATS) -> list[dict]:
    """슬롯 목록을 만든다. 같은 입력이면 같은 출력이다. 입력을 바꾸지 않는다.

    pool은 `per_bucket=10`(60슬롯), pilot은 `per_bucket=1`(6슬롯)이다.
    """
    topics = group_topics(rows)
    buckets = list(dict.fromkeys(t["bucket"] for t in topics))
    slots: list[dict] = []
    g = 0
    for b in buckets:
        examinable = [t for t in topics if t["bucket"] == b and t["status"] != MISSING]
        if not examinable:
            raise ValueError(f"bucket {b}: no examinable topic")
        bucket_formats = [formats[(g + k) % len(formats)] for k in range(per_bucket)]
        g += per_bucket
        counters = {"code": 0, "mcp": 0, "short": 0, "other": 0}
        for t, f in _assign_topics(b, bucket_formats, examinable):
            if f == CODE_FORMAT:
                qtype = TYPES_CODE[counters["code"] % len(TYPES_CODE)]
                counters["code"] += 1
                pages = [p for p in t["pages"] if p not in t["mcp_pages"]]
            elif t["is_mcp"]:
                qtype = TYPES_MCP[counters["mcp"] % len(TYPES_MCP)]
                counters["mcp"] += 1
                pages = list(t["pages"])
            elif f == "short":
                qtype = TYPES_SHORT[counters["short"] % len(TYPES_SHORT)]
                counters["short"] += 1
                pages = list(t["pages"])
            else:
                qtype = TYPES_OTHER[counters["other"] % len(TYPES_OTHER)]
                counters["other"] += 1
                pages = list(t["pages"])
            slots.append({
                "bucket": b,
                "topic_no": t["topic_no"],
                "topic": t["topic"],
                "format": f,
                "question_type": qtype,
                "status": t["status"],
                "near": t["status"] == NEAR,
                "near_pages": [p for p in pages if p in t["near_pages"]],
                "pages": pages,
            })
    return slots
