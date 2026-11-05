"""슬롯 1개를 처리하는 LangGraph 그래프(design.md 6.1).

generate → judge → (코드형이면 execute) → gates → dedupe → record.
record가 판정한다. 통과하거나 버리면 끝나고, 아니면 feedback을 거쳐 generate로 돌아간다(최대 3회 재생성).
"""

from langgraph.graph import END, START, StateGraph

from quiz.pipeline import nodes
from quiz.pipeline.nodes import SlotState

# 시도 1회 = 노드 최대 7개. 4회 시도에 여유를 둔다
RECURSION_LIMIT = 50


def _after_judge(state: SlotState) -> str:
    return "execute" if state["slot"]["format"] == nodes.CODE_FORMAT else "gates"


def _after_record(state: SlotState) -> str:
    return END if state.get("status") else "feedback"


def build_graph(gen_model=None, judge_model=None, gate_fn=None, run=None):
    """gate_fn, run: 테스트에서 결정적 게이트와 샌드박스 실행을 바꿔 끼운다."""
    g = StateGraph(SlotState)
    g.add_node("generate", lambda s: nodes.generate(s, gen_model))
    g.add_node("judge", lambda s: nodes.judge(s, judge_model))
    g.add_node("execute", lambda s: nodes.execute(s, run))
    g.add_node("gates", lambda s: nodes.run_gates(s, gate_fn))
    g.add_node("dedupe", nodes.dedupe)
    g.add_node("record", nodes.record)
    g.add_node("feedback", nodes.feedback)
    g.add_edge(START, "generate")
    g.add_edge("generate", "judge")
    g.add_conditional_edges("judge", _after_judge, ["execute", "gates"])
    g.add_edge("execute", "gates")
    g.add_edge("gates", "dedupe")
    g.add_edge("dedupe", "record")
    g.add_conditional_edges("record", _after_record, ["feedback", END])
    g.add_edge("feedback", "generate")
    return g.compile()


def run(graph, state: SlotState) -> SlotState:
    return graph.invoke(state, {"recursion_limit": RECURSION_LIMIT})
