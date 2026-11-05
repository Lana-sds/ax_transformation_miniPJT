"""생성 배치 실행(design.md 6.2).

M0 임시: 슬롯 계획은 허용 목록 첫 행에서 단일 선택 슬롯을 만든다. 재생성 없이 1회 시도한다.
실패하면 첫 실패 이유를 `drop_reason`으로 두고 버린다. T1.7(슬롯 계획), T2.3(재생성), T2.7(재개)에서 바꾼다.
"""

from quiz import allowlist, db, llm, store
from quiz.backup import backup
from quiz.migrate import apply_migrations
from quiz.pipeline.graph import build_graph, verdict


def m0_slots(rows: list[dict], count: int) -> list[dict]:
    row = next(r for r in rows if r.get("snapshot"))  # M0 임시: 스냅샷이 있는 첫 행. T2.7에서 슬롯 계획으로 바꾼다
    return [
        {"bucket": row["bucket"], "topic": row["topic"], "format": "single", "question_type": "concept",
         "pages": [row["path"]], "near": False, "near_pages": []}
        for _ in range(count)
    ]


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
        row = by_path[slot["pages"][0]]
        state = graph.invoke({
            "slot": slot,
            "snapshots": {p: allowlist.read_snapshot(by_path[p]) for p in slot["pages"]},
            "fetched": {p: by_path[p]["fetched_at"] for p in slot["pages"]},
            "allowed_pages": pages,
        })
        qid = store.question_id(batch_id, no)
        status = verdict(state)
        reasons = state.get("fail_reasons") or []
        with db.connect() as conn:
            store.upsert_question(
                conn, qid, batch_id, slot, state.get("question"),
                status="passed" if status == "passed" else "dropped",
                drop_reason=None if status == "passed" else reasons[0],
                regen_count=0, fetched_at=row["fetched_at"],
            )
            store.upsert_verification(conn, qid, 0, state)
        print(f"{qid} {status} {reasons}")
    with db.connect() as conn:
        store.finish_batch(conn, batch_id)
    return batch_id
