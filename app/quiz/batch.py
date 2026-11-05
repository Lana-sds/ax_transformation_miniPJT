"""생성 배치 실행(design.md 6.2).

M0 임시: 슬롯 계획은 허용 목록 첫 행에서 단일 선택 슬롯을 만든다. T2.7(슬롯 계획, 재개)에서 바꾼다.
"""

from quiz import allowlist, db, llm, store
from quiz.backup import backup
from quiz.migrate import apply_migrations
from quiz.pipeline import graph as slot_graph
from quiz.pipeline.graph import build_graph


def m0_slots(rows: list[dict], count: int) -> list[dict]:
    row = next(r for r in rows if r.get("snapshot"))  # M0 임시: 스냅샷이 있는 첫 행. T2.7에서 슬롯 계획으로 바꾼다
    return [
        {"bucket": row["bucket"], "topic": row["topic"], "format": "single", "question_type": "concept",
         "pages": [row["path"]], "near": False, "near_pages": []}
        for _ in range(count)
    ]


def process_slot(graph, batch_id: str, slot_no: int, slot: dict, snapshots: dict[str, str],
                 fetched: dict[str, str], allowed_pages: set[str]) -> dict:
    """슬롯 1개를 끝까지 돌리고(재생성 포함) 문제 1행과 시도별 검증 행을 쓴다."""
    qid = store.question_id(batch_id, slot_no)
    with db.connect() as conn:
        peers = store.passed_in_bucket(conn, slot["bucket"], exclude_qid=qid)
    state = slot_graph.run(graph, {
        "slot": slot, "snapshots": snapshots, "fetched": fetched, "allowed_pages": allowed_pages,
        "peers": peers, "regen_count": 0, "attempts": [],
    })
    question = state.get("question")
    fetched_at = (question or {}).get("fetched_at") or min(fetched.values())
    with db.connect() as conn:
        store.upsert_question(
            conn, qid, batch_id, slot, question, status=state["status"], drop_reason=state.get("drop_reason"),
            regen_count=state.get("regen_count") or 0, fetched_at=fetched_at,
        )
        for attempt_no, attempt in enumerate(state["attempts"]):
            store.upsert_verification(conn, qid, attempt_no, attempt)
    return state


def run_batch(count: int) -> str:
    backup(db.db_path(), "batch")
    rows = allowlist.load_rows()
    allowlist.verify(rows)
    pages = allowlist.allowed_pages(rows)
    by_path = {r["path"]: r for r in rows}
    slots = m0_slots(rows, count)
    graph = build_graph()

    with db.connect() as conn:
        apply_migrations(conn)
        batch_id = store.next_batch_id(conn)
        store.insert_batch(conn, batch_id, "pool", llm.GEN_MODEL, llm.JUDGE_MODEL)
        store.insert_slots(conn, batch_id, slots)
    for no, slot in enumerate(slots, start=1):
        state = process_slot(
            graph, batch_id, no, slot,
            {p: allowlist.read_snapshot(by_path[p]) for p in slot["pages"]},
            {p: by_path[p]["fetched_at"] for p in slot["pages"]},
            pages,
        )
        print(f"{store.question_id(batch_id, no)} {state['status']} {state.get('drop_reason') or ''}")
    with db.connect() as conn:
        store.finish_batch(conn, batch_id)
    return batch_id
