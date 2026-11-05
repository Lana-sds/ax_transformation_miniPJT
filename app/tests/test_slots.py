"""슬롯 계획(design.md 6.1, US-2.4) 테스트. DB와 모델 호출 없이 page-allowlist.md만 읽는다."""

from collections import Counter

import pytest

from quiz import slots

BUCKETS = ["rag", "langgraph_basics", "tool_mcp", "middleware_hitl_guardrails", "multi_agent", "ops_quality"]
FORMATS = ["single", "multi", "short", "code"]


@pytest.fixture(scope="module")
def rows():
    return slots.load_allowlist_md()


@pytest.fixture(scope="module")
def topics(rows):
    return slots.group_topics(rows)


@pytest.fixture(scope="module")
def pool(rows):
    return slots.plan_slots(rows)


def _topic(topics, bucket, no):
    return next(t for t in topics if t["bucket"] == bucket and t["topic_no"] == no)


# --- page-allowlist.md 읽기 ---

def test_loader_reads_all_buckets_and_topics(topics):
    assert [b for b in BUCKETS] == list(dict.fromkeys(t["bucket"] for t in topics))
    per_bucket = Counter(t["bucket"] for t in topics)
    # page-allowlist.md "요약" 표의 주제 수
    assert per_bucket == {"rag": 7, "langgraph_basics": 6, "tool_mcp": 6,
                          "middleware_hitl_guardrails": 5, "multi_agent": 5, "ops_quality": 5}


def test_topic_status_matches_summary_table(topics):
    # 요약 표: 확인 30, 근접만 3, 없음 1. 재랭킹은 확인 행과 근접 행이 섞여 확인으로 센다
    assert Counter(t["status"] for t in topics) == {"확인": 30, "근접": 3, "없음": 1}
    assert {(t["bucket"], t["topic_no"]) for t in topics if t["status"] == "근접"} == {
        ("langgraph_basics", 5), ("multi_agent", 3), ("ops_quality", 1)}
    assert [(t["bucket"], t["topic_no"]) for t in topics if t["status"] == "없음"] == [("tool_mcp", 3)]
    assert _topic(topics, "rag", 7)["status"] == "확인"


def test_mcp_rows_match_tool_mcp_note(rows, topics):
    # 노트: "MCP 행(#4, #5, #6의 `mcp/tools`)"
    mcp_rows = {(r["bucket"], r["topic_no"], r["path"]) for r in rows if slots.is_mcp_row(r)}
    assert {(b, n) for b, n, _ in mcp_rows} == {("tool_mcp", 4), ("tool_mcp", 5), ("tool_mcp", 6)}
    assert [p for b, n, p in mcp_rows if n == 6] == ["/oss/python/langchain/mcp/tools"]
    assert len([1 for _, n, _ in mcp_rows if n in (4, 5)]) == 6
    # 주제 단위 MCP는 모든 행이 MCP인 #4, #5다. #6 장애 주입은 MCP 행만 빼고 코드형을 낸다(6.1)
    assert {(t["bucket"], t["topic_no"]) for t in topics if t["is_mcp"]} == {("tool_mcp", 4), ("tool_mcp", 5)}


# --- 60슬롯 풀 계획 (T1.7 확인) ---

def test_pool_has_60_slots_10_per_bucket(pool):
    assert len(pool) == 60
    assert Counter(s["bucket"] for s in pool) == {b: 10 for b in BUCKETS}
    assert [s["bucket"] for s in pool] == sorted((s["bucket"] for s in pool), key=BUCKETS.index)


def test_pool_each_format_at_least_10(pool):
    by_format = Counter(s["format"] for s in pool)
    assert set(by_format) == set(FORMATS)
    assert all(by_format[f] >= 10 for f in FORMATS), by_format


def test_pool_each_bucket_rotates_formats_2_to_3(pool):
    for b in BUCKETS:
        counts = Counter(s["format"] for s in pool if s["bucket"] == b)
        assert set(counts) == set(FORMATS)
        assert all(2 <= c <= 3 for c in counts.values()), (b, counts)


def test_pool_no_code_on_mcp_or_missing_topics(pool, topics):
    forbidden = {(t["bucket"], t["topic"]) for t in topics if t["is_mcp"] or t["status"] == "없음"}
    bad = [s for s in pool if s["format"] == "code" and (s["bucket"], s["topic"]) in forbidden]
    assert bad == []


def test_pool_no_slot_on_missing_topics(pool, topics):
    missing = {(t["bucket"], t["topic"]) for t in topics if t["status"] == "없음"}
    assert [s for s in pool if (s["bucket"], s["topic"]) in missing] == []


def test_pool_code_slots_never_cite_mcp_pages(pool, rows):
    mcp_paths = {r["path"] for r in rows if slots.is_mcp_row(r)}
    for s in pool:
        assert s["pages"], s
        if s["format"] == "code":
            assert not set(s["pages"]) & mcp_paths, s


def test_pool_near_flag_matches_topic_status(pool, topics):
    status = {(t["bucket"], t["topic"]): t["status"] for t in topics}
    for s in pool:
        assert s["near"] is (status[(s["bucket"], s["topic"])] == "근접")
    assert {s["topic_no"] for s in pool if s["near"] and s["bucket"] == "langgraph_basics"} == {5}
    assert any(s["near"] for s in pool if s["bucket"] == "multi_agent")
    assert any(s["near"] for s in pool if s["bucket"] == "ops_quality")


def test_pool_near_pages_listed(pool):
    rerank = [s for s in pool if s["bucket"] == "rag" and s["topic_no"] == 7]
    assert rerank
    for s in rerank:
        assert s["near"] is False
        assert s["near_pages"] == ["/oss/python/integrations/retrievers"]


def test_pool_question_types(pool, topics):
    mcp = {(t["bucket"], t["topic"]) for t in topics if t["is_mcp"]}
    for s in pool:
        assert s["question_type"] in {"concept", "code_behavior", "error_cause", "design"}
        if (s["bucket"], s["topic"]) in mcp:
            assert s["question_type"] in {"concept", "design"}, s
        if s["format"] == "code":
            assert s["question_type"] in {"code_behavior", "error_cause"}, s
        if s["format"] == "short":
            assert s["question_type"] != "code_behavior", s
    assert {s["question_type"] for s in pool} == {"concept", "code_behavior", "error_cause", "design"}


def test_pool_covers_every_examinable_topic(pool, topics):
    examinable = {(t["bucket"], t["topic"]) for t in topics if t["status"] != "없음"}
    assert {(s["bucket"], s["topic"]) for s in pool} == examinable


def test_pool_is_deterministic(rows):
    assert slots.plan_slots(rows) == slots.plan_slots(list(rows))
    assert slots.plan_slots(rows) == slots.plan_slots(list(reversed(rows)))


def test_pilot_is_one_per_bucket_covering_all_formats(rows):
    pilot = slots.plan_slots(rows, per_bucket=1)
    assert [s["bucket"] for s in pilot] == BUCKETS
    assert set(s["format"] for s in pilot) == set(FORMATS)
    assert all(s["status"] != "없음" for s in pilot)


# --- 작은 합성 입력 ---

def _row(bucket, no, topic, path, status="확인", kind="docs"):
    return {"bucket": bucket, "topic_no": no, "topic": topic, "path": path, "kind": kind, "status": status}


SYNTH = [
    _row("tool_mcp", 1, "@tool", "/tools"),
    _row("tool_mcp", 2, "MCP client", "/langchain/mcp"),
    _row("tool_mcp", 3, "server", None, status="없음", kind=None),
    _row("multi_agent", 1, "hier", "/subgraphs", status="근접"),
    _row("multi_agent", 2, "router", "/router"),
]


def test_synthetic_topic_grouping_and_status():
    rows = [_row("rag", 1, "t", "/a", "근접"), _row("rag", 1, "t", "/b", "확인"),
            _row("rag", 2, "u", "/c", "근접"), _row("rag", 3, "v", None, "없음", None)]
    ts = slots.group_topics(rows)
    assert [(t["topic"], t["status"]) for t in ts] == [("t", "확인"), ("u", "근접"), ("v", "없음")]
    assert ts[0]["pages"] == ["/a", "/b"]
    assert ts[2]["pages"] == []


def test_synthetic_plan_counts_and_forbidden():
    plan = slots.plan_slots(SYNTH, per_bucket=4)
    assert Counter(s["bucket"] for s in plan) == {"multi_agent": 4, "tool_mcp": 4}
    assert [s["bucket"] for s in plan[:4]] == ["tool_mcp"] * 4  # 버킷 순서는 BUCKETS 순서
    assert all(s["topic"] != "server" for s in plan)
    assert all(not (s["format"] == "code" and s["topic"] == "MCP client") for s in plan)
    assert Counter(s["format"] for s in plan) == {f: 2 for f in FORMATS}
    near = [s for s in plan if s["topic"] == "hier"]
    assert near and all(s["near"] for s in near)
    assert all(not s["near"] for s in plan if s["topic"] != "hier")


def test_synthetic_mcp_flag_from_row():
    rows = [_row("tool_mcp", 1, "a", "/x", ), _row("tool_mcp", 2, "b", "/y")]
    rows[1]["is_mcp"] = True
    ts = slots.group_topics(rows)
    assert [t["is_mcp"] for t in ts] == [False, True]


def test_synthetic_code_needs_eligible_topic():
    rows = [_row("tool_mcp", 1, "MCP client", "/langchain/mcp")]
    with pytest.raises(ValueError):
        slots.plan_slots(rows, per_bucket=4)


def test_synthetic_bucket_without_examinable_topic_fails():
    with pytest.raises(ValueError):
        slots.plan_slots([_row("rag", 1, "x", None, "없음", None)], per_bucket=1)


def test_synthetic_deterministic_and_input_not_mutated():
    import copy
    before = copy.deepcopy(SYNTH)
    a = slots.plan_slots(SYNTH, per_bucket=4)
    b = slots.plan_slots(list(reversed(SYNTH)), per_bucket=4)
    assert a == b
    assert SYNTH == before
