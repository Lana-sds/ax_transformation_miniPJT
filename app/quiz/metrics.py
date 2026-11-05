"""기준선 지표(design.md 5.4, requirements 7.3). SQLite에서 `data/metrics/baseline.json`을 다시 만든다."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from quiz.db import DATA_DIR
from quiz.pool import current_pool
from quiz.store import now

BASELINE_PATH = DATA_DIR / "metrics" / "baseline.json"


def _rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def _seconds(started: str | None, finished: str | None) -> int | None:
    if not started or not finished:
        return None
    parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: E731
    return int((parse(finished) - parse(started)).total_seconds())


def build(conn: sqlite3.Connection) -> dict:
    # Judge를 거친 시도: judge_pass가 기록된 시도 행
    attempts, passed = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(judge_pass = 1), 0) FROM verification_results WHERE judge_pass IS NOT NULL"
    ).fetchone()

    by_reason = {r[0]: r[1] for r in conn.execute(
        "SELECT drop_reason, COUNT(*) FROM questions WHERE status = 'dropped' GROUP BY drop_reason ORDER BY drop_reason"
    )}

    psid = current_pool(conn)
    sets = []
    for r in conn.execute(
        "SELECT set_id, set_no, question_ids_json FROM quiz_sets WHERE pool_snapshot_id = ? ORDER BY set_no", (psid,)
    ):
        total = len(json.loads(r["question_ids_json"]))
        correct = conn.execute(
            "SELECT COALESCE(SUM(correct), 0) FROM attempts WHERE set_id = ?", (r["set_id"],)
        ).fetchone()[0]
        sets.append({"set_no": r["set_no"], "set_id": r["set_id"], "correct": correct, "total": total,
                     "rate": _rate(correct, total)})

    batches = [
        {"batch_id": r["batch_id"], "kind": r["kind"], "input_tokens": r["input_tokens"],
         "output_tokens": r["output_tokens"], "cost_usd": r["cost_usd"],
         "seconds": _seconds(r["started_at"], r["finished_at"])}
        for r in conn.execute("SELECT * FROM batches ORDER BY batch_id")
    ]

    return {
        "generated_at": now(),
        "pool_snapshot_id": psid,
        "judge_pass_rate": {"attempts": attempts, "passed": passed, "rate": _rate(passed, attempts)},
        "drops": {"total": sum(by_reason.values()), "by_reason": by_reason},
        "sets": sets,
        "batches": batches,
    }


def write(conn: sqlite3.Connection, path: Path | None = None) -> Path:
    path = path or BASELINE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(conn), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
