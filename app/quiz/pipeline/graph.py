"""슬롯 1개를 처리하는 LangGraph 그래프(design.md 6.1).

M0: generate → judge → gates. 재생성, 실행(코드형), 중복 검사는 M2에서 붙인다.
"""

from langgraph.graph import END, START, StateGraph

from quiz.pipeline import nodes
from quiz.pipeline.nodes import SlotState


def build_graph(gen_model=None, judge_model=None):
    g = StateGraph(SlotState)
    g.add_node("generate", lambda s: nodes.generate(s, gen_model))
    g.add_node("judge", lambda s: nodes.judge(s, judge_model))
    g.add_node("gates", nodes.run_gates)
    g.add_edge(START, "generate")
    g.add_edge("generate", "judge")
    g.add_edge("judge", "gates")
    g.add_edge("gates", END)
    return g.compile()


def verdict(state: SlotState) -> str:
    """최종 판정. 실패 이유가 없으면 passed."""
    return "passed" if not state.get("fail_reasons") else "failed"
