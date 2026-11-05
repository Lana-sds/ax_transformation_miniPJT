"""재생성 루프(T2.3)와 dedupe·노드 순서(T2.6), design.md 6.1. 모델과 게이트는 가짜로 바꾼다."""

import json

from llm_fakes import FakeModel
from quiz import batch, store
from quiz.pipeline import nodes
from quiz.pipeline.graph import build_graph
from test_generate import PAGE, payload
from test_judge import PASS

BATCH = "b20261105-01"
SLOT = {"bucket": "langgraph_basics", "topic": "StateGraph", "format": "single", "question_type": "concept",
        "pages": [PAGE], "near": False, "near_pages": []}


def always(fails):
    return lambda *args, **kwargs: list(fails)


def sequence(*results):
    calls = []

    def gate(*args, **kwargs):
        calls.append(1)
        return list(results[min(len(calls) - 1, len(results) - 1)])
    return gate


def setup_batch(conn, slots):
    store.insert_batch(conn, BATCH, "pool", "gen", "judge")
    store.insert_slots(conn, BATCH, slots)
    conn.commit()


def process(graph, no, slot=SLOT):
    return batch.process_slot(graph, BATCH, no, slot, {PAGE: "DOC"}, {PAGE: "2026-11-05"}, {PAGE})


def question_row(conn, qid):
    return conn.execute("SELECT status, drop_reason, regen_count FROM questions WHERE question_id = ?",
                        (qid,)).fetchone()


def attempts(conn, qid):
    return conn.execute(
        "SELECT attempt_no, fail_reasons_json, input_tokens, duplicate_of FROM verification_results "
        "WHERE question_id = ? ORDER BY attempt_no", (qid,)).fetchall()


# --- T2.3 ---

def test_always_failing_gate_leaves_four_attempts_and_regen_exhausted(tmp_db):
    setup_batch(tmp_db, [SLOT])
    graph = build_graph(FakeModel(payload("single")), FakeModel(PASS), gate_fn=always(["quote_mismatch"]))
    process(graph, 1)
    qid = store.question_id(BATCH, 1)
    assert tuple(question_row(tmp_db, qid)) == ("dropped", "regen_exhausted", 3)
    rows = attempts(tmp_db, qid)
    assert [r[0] for r in rows] == [0, 1, 2, 3]
    assert all(json.loads(r[1]) == ["quote_mismatch"] for r in rows)


def test_each_attempt_row_has_its_own_tokens(tmp_db):
    setup_batch(tmp_db, [SLOT])
    graph = build_graph(FakeModel(payload("single")), FakeModel(PASS), gate_fn=always(["quote_mismatch"]))
    process(graph, 1)
    # 시도마다 생성 100 + Judge 100. 누적하지 않는다
    assert [r[2] for r in attempts(tmp_db, store.question_id(BATCH, 1))] == [200, 200, 200, 200]


def test_fail_reasons_go_into_next_generate_prompt(tmp_db):
    setup_batch(tmp_db, [SLOT])
    gen = FakeModel(payload("single"))
    graph = build_graph(gen, FakeModel(PASS), gate_fn=sequence(["quote_mismatch"], []))
    process(graph, 1)
    assert "quote_mismatch" not in gen.prompts[0]
    assert "quote_mismatch" in gen.prompts[1]
    assert tuple(question_row(tmp_db, store.question_id(BATCH, 1))) == ("passed", None, 1)


def test_judge_reasons_go_into_feedback(tmp_db):
    setup_batch(tmp_db, [SLOT])
    gen = FakeModel(payload("single"))
    fail = PASS | {"distractors_wrong": False, "verdict": "fail", "reasons": ["choice D is also correct"]}
    graph = build_graph(gen, FakeModel([fail, PASS]), gate_fn=always([]))
    process(graph, 1)
    assert "judge_fail:distractors_wrong" in gen.prompts[1]
    assert "choice D is also correct" in gen.prompts[1]


def test_schema_invalid_regenerates(tmp_db):
    setup_batch(tmp_db, [SLOT])
    graph = build_graph(FakeModel([None, payload("single")]), FakeModel(PASS), gate_fn=always([]))
    process(graph, 1)
    qid = store.question_id(BATCH, 1)
    assert tuple(question_row(tmp_db, qid)) == ("passed", None, 1)
    assert json.loads(attempts(tmp_db, qid)[0][1]) == ["schema_invalid"]


# --- T2.6 ---

def test_same_quote_twice_second_is_duplicate_without_regen(tmp_db):
    setup_batch(tmp_db, [SLOT, SLOT])
    gen = FakeModel(payload("single"))
    graph = build_graph(gen, FakeModel(PASS), gate_fn=always([]))
    process(graph, 1)
    process(graph, 2)
    first, second = store.question_id(BATCH, 1), store.question_id(BATCH, 2)
    assert question_row(tmp_db, first)[0] == "passed"
    assert tuple(question_row(tmp_db, second)) == ("dropped", "duplicate", 0)
    rows = attempts(tmp_db, second)
    assert len(rows) == 1
    assert rows[0][3] == first
    assert len(gen.prompts) == 2  # 두 번째 슬롯은 재생성하지 않았다


def test_duplicate_only_within_same_bucket(tmp_db):
    other = SLOT | {"bucket": "agents"}
    setup_batch(tmp_db, [SLOT, other])
    graph = build_graph(FakeModel(payload("single")), FakeModel(PASS), gate_fn=always([]))
    process(graph, 1)
    process(graph, 2, other)
    assert question_row(tmp_db, store.question_id(BATCH, 2))[0] == "passed"


def code_slot():
    return SLOT | {"format": "code", "question_type": "code_behavior"}


def test_version_conflict_drops_without_regen(tmp_db):
    slot = code_slot()
    setup_batch(tmp_db, [slot])
    preds = [{"choice_id": c, **e["expected"]} for c, e in zip("ABCD", payload("code")["exec_spec"])]
    broken = {"ok": False, "stdout": "", "error_type": "ImportError"}
    gen = FakeModel(payload("code"))
    graph = build_graph(gen, FakeModel(PASS | {"exec_predictions": preds}), gate_fn=always([]),
                        run=lambda code: broken)
    process(graph, 1, slot)
    assert tuple(question_row(tmp_db, store.question_id(BATCH, 1))) == ("dropped", "version_conflict", 0)
    assert len(gen.prompts) == 1


def test_node_order_generate_judge_execute_gates_dedupe():
    graph = build_graph(FakeModel(payload("single")), FakeModel(PASS))
    nodes = list(graph.get_graph().nodes)
    for a, b in [("generate", "judge"), ("judge", "execute"), ("execute", "gates"), ("gates", "dedupe")]:
        assert nodes.index(a) < nodes.index(b)
    edges = {(e.source, e.target) for e in graph.get_graph().edges}
    assert {("generate", "judge"), ("execute", "gates"), ("gates", "dedupe"), ("feedback", "generate")} <= edges
    assert ("judge", "execute") in edges and ("judge", "gates") in edges


def test_non_code_skips_execute(tmp_db):
    setup_batch(tmp_db, [SLOT])
    called = []
    graph = build_graph(FakeModel(payload("single")), FakeModel(PASS), gate_fn=always([]),
                        run=lambda code: called.append(code))
    process(graph, 1)
    assert called == []


def test_feedback_quote_mismatch_shows_quote_and_source():
    from test_gates import LINK_SNAPSHOT
    bad = "Chat mode is only supported for graph's whose state includes or extends `MessagesState`."
    good = "Chat mode is a simpler UI. Chat mode is only"
    state = {
        "fail_reasons": ["quote_mismatch"], "judge": None, "regen_count": 0,
        "snapshots": {"/langsmith/studio": LINK_SNAPSHOT},
        "question": {"grounding_records": [{"page": "/langsmith/studio", "quote": good},
                                           {"page": "/langsmith/studio", "quote": bad}]},
    }
    fb = nodes.feedback(state)["feedback"]
    assert fb[0] == "quote_mismatch"
    text = "\n".join(fb)
    assert bad in text
    assert good not in text
    assert "[`MessagesState`](/oss/python/langgraph/graph-api-state#messagesstate)" in text
    assert "markdown link" in text and "code fence" in text


def test_feedback_without_quote_mismatch_has_no_quote_hint():
    fb = nodes.feedback({"fail_reasons": ["mapping_missing"], "judge": None, "regen_count": 0})["feedback"]
    assert fb == ["mapping_missing"]
