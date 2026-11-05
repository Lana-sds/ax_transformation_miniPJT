"""생성 배치 실행(design.md 6.2).

- 시작할 때 슬롯 목록을 `batch_slots`에 먼저 쓴다. `pilot`은 버킷당 1슬롯(6), `pool`은 60슬롯이다.
- 슬롯 사이 동시 실행은 2개다(8.1). 슬롯 하나가 예외로 멈춰도 나머지는 돈다.
- 모든 슬롯이 `passed`·`dropped`가 되어야 `finished_at`을 채운다.
- `--resume <batch_id>`는 `batch_slots`에서 `passed`·`dropped`가 아닌 슬롯만 처음부터 다시 돈다.
  슬롯의 근거 페이지는 허용 목록에서 다시 만든다(`slots.slot_for`).
"""

import traceback
from concurrent.futures import ThreadPoolExecutor

from quiz import allowlist, db, llm, slots, store
from quiz.backup import backup
from quiz.migrate import apply_migrations
from quiz.pipeline import graph as slot_graph
from quiz.pipeline.graph import build_graph

WORKERS = 2
DONE = ("passed", "dropped")
PER_BUCKET = {"pilot": 1, "pool": 10}


def make_plan(rows: list[dict], kind: str, count: int | None = None) -> list[dict]:
    planned = slots.plan_slots(rows, per_bucket=PER_BUCKET[kind])
    return planned[:count] if count is not None else planned


def process_slot(graph, batch_id: str, slot_no: int, slot: dict, snapshots: dict[str, str],
                 fetched: dict[str, str], allowed_pages: set[str]) -> dict:
    """슬롯 1개를 끝까지 돌리고(재생성 포함) 문제 1행과 시도별 검증 행을 쓴다."""
    qid = store.question_id(batch_id, slot_no)
    with db.connect() as conn:
        peers = store.passed_in_bucket(conn, slot["bucket"], exclude_qid=qid)
    state = slot_graph.run(graph, {
        "slot": slot, "snapshots": snapshots, "fetched": fetched, "allowed_pages": allowed_pages,
        "peers": peers, "regen_count": 0, "attempts": [],
    }, llm.trace_config(batch_id))
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


def unfinished(batch_id: str) -> int:
    with db.connect() as conn:
        return sum(1 for s in store.batch_slots(conn, batch_id) if s["status"] not in DONE)


def run_batch(plan: str | None = None, count: int | None = None, resume: str | None = None,
              gen_model=None, judge_model=None, gate_fn=None, run=None, workers: int = WORKERS) -> str:
    """배치를 새로 돌리거나(`plan`) 이어 돈다(`resume`). batch_id를 돌려준다."""
    backup(db.db_path(), "batch")
    rows = allowlist.load_rows()
    allowlist.verify(rows)
    pages = allowlist.allowed_pages(rows)
    by_path = {r["path"]: r for r in rows}

    with db.connect() as conn:
        apply_migrations(conn)
        if resume is None:
            planned = make_plan(rows, plan, count)
            batch_id = store.next_batch_id(conn)
            store.insert_batch(conn, batch_id, "pool", llm.GEN_MODEL, llm.JUDGE_MODEL)
            store.insert_slots(conn, batch_id, planned)
        else:
            batch_id = resume
        todo = [(s["slot_no"], slots.slot_for(rows, s["bucket"], s["topic"], s["format"], s["question_type"]))
                for s in store.batch_slots(conn, batch_id) if s["status"] not in DONE]
    print(f"batch_id={batch_id} slots_to_run={len(todo)}", flush=True)

    graph = build_graph(gen_model, judge_model, gate_fn=gate_fn, run=run)

    def one(item):
        no, slot = item
        qid = store.question_id(batch_id, no)
        try:
            state = process_slot(
                graph, batch_id, no, slot,
                {p: allowlist.read_snapshot(by_path[p]) for p in slot["pages"]},
                {p: by_path[p]["fetched_at"] for p in slot["pages"]},
                pages,
            )
        except Exception as e:  # 한 슬롯 실패로 배치를 멈추지 않는다. 재개 때 다시 돈다
            print(f"{qid} error {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
            return
        print(f"{qid} {state['status']} {state.get('drop_reason') or ''} regen={state.get('regen_count')}",
              flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, todo))

    with db.connect() as conn:
        store.finish_batch(conn, batch_id, done=unfinished(batch_id) == 0)
    llm.flush_traces()
    return batch_id
