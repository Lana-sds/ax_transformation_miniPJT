"""생성 배치 결과 쓰기(design.md 5.1, 6.2). 쓰기는 upsert다(D-13)."""

import json
import sqlite3
from datetime import UTC, datetime


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _j(value) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False)


def next_batch_id(conn: sqlite3.Connection, day: str | None = None) -> str:
    day = day or datetime.now(UTC).strftime("%Y%m%d")
    prefix = f"b{day}-"
    rows = conn.execute("SELECT batch_id FROM batches WHERE batch_id LIKE ?", (prefix + "%",)).fetchall()
    seq = max((int(r[0].rsplit("-", 1)[1]) for r in rows), default=0) + 1
    return f"{prefix}{seq:02d}"


def question_id(batch_id: str, slot_no: int) -> str:
    return f"{batch_id}-{slot_no:03d}"


def insert_batch(conn, batch_id: str, kind: str, gen_model: str, judge_model: str) -> None:
    conn.execute(
        "INSERT INTO batches (batch_id, kind, started_at, gen_model, judge_model) VALUES (?, ?, ?, ?, ?)",
        (batch_id, kind, now(), gen_model, judge_model),
    )


def insert_slots(conn, batch_id: str, slots: list[dict]) -> None:
    for no, s in enumerate(slots, start=1):
        conn.execute(
            """INSERT INTO batch_slots (batch_id, slot_no, bucket, topic, format, question_type, variant_of, question_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (batch_id, slot_no) DO NOTHING""",
            (batch_id, no, s["bucket"], s["topic"], s["format"], s["question_type"], s.get("variant_of"),
             question_id(batch_id, no)),
        )


def upsert_question(conn, qid: str, batch_id: str, slot: dict, question: dict | None,
                    status: str, drop_reason: str | None, regen_count: int, fetched_at: str) -> None:
    q = question or {}
    ts = now()
    conn.execute(
        """INSERT INTO questions (question_id, batch_id, bucket, topic, format, question_type, select_count,
               cca_f_tag, stem_en, choices_json, answer_key_json, accepted_answers_json, explanation_ko,
               segments_json, exec_spec_json, doc_url, status, drop_reason, regen_count, variant_of,
               fetched_at, lock_hash, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (question_id) DO UPDATE SET
               select_count = excluded.select_count, cca_f_tag = excluded.cca_f_tag, stem_en = excluded.stem_en,
               choices_json = excluded.choices_json, answer_key_json = excluded.answer_key_json,
               accepted_answers_json = excluded.accepted_answers_json, explanation_ko = excluded.explanation_ko,
               segments_json = excluded.segments_json, exec_spec_json = excluded.exec_spec_json,
               doc_url = excluded.doc_url, status = excluded.status, drop_reason = excluded.drop_reason,
               regen_count = excluded.regen_count, fetched_at = excluded.fetched_at,
               lock_hash = excluded.lock_hash, updated_at = excluded.updated_at""",
        (qid, batch_id, slot["bucket"], slot["topic"], slot["format"], slot["question_type"],
         q.get("select_count"), q.get("cca_f_tag", "n/a"), q.get("stem_en", ""), _j(q.get("choices")),
         _j(q.get("answer_key", [])), _j(q.get("accepted_answers")), q.get("explanation_ko", ""),
         _j(q.get("segments", [])), _j(q.get("exec_spec")), q.get("doc_url"), status, drop_reason,
         regen_count, slot.get("variant_of"), fetched_at, q.get("lock_hash"), ts, ts),
    )
    conn.execute("DELETE FROM grounding_records WHERE question_id = ?", (qid,))
    for idx, rec in enumerate(q.get("grounding_records", [])):
        conn.execute(
            "INSERT INTO grounding_records (question_id, idx, page, quote, fetched_at, answer_basis) VALUES (?, ?, ?, ?, ?, ?)",
            (qid, idx, rec["page"], rec["quote"], fetched_at, rec.get("answer_basis", "")),
        )


def upsert_verification(conn, qid: str, attempt_no: int, state: dict) -> None:
    gate_fails = state.get("gate_fails") or []
    judge = state.get("judge")
    question = state.get("question")
    tokens = state.get("tokens") or {}
    quote_match = None if question is None else int(not any(f.startswith("quote_") or f == "page_not_allowed" for f in gate_fails))
    mapping_present = None if question is None else int("mapping_missing" not in gate_fails)
    judge_pass = None if judge is None else int(judge.get("verdict") == "pass")
    conn.execute(
        """INSERT INTO verification_results (question_id, attempt_no, quote_match, mapping_present, judge_pass,
               exec_match, duplicate_of, judge_verdict_json, exec_result_json, fail_reasons_json,
               input_tokens, output_tokens, cost_usd, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (question_id, attempt_no) DO UPDATE SET
               quote_match = excluded.quote_match, mapping_present = excluded.mapping_present,
               judge_pass = excluded.judge_pass, exec_match = excluded.exec_match,
               duplicate_of = excluded.duplicate_of, judge_verdict_json = excluded.judge_verdict_json,
               exec_result_json = excluded.exec_result_json, fail_reasons_json = excluded.fail_reasons_json,
               input_tokens = excluded.input_tokens, output_tokens = excluded.output_tokens,
               cost_usd = excluded.cost_usd, created_at = excluded.created_at""",
        (qid, attempt_no, quote_match, mapping_present, judge_pass, state.get("exec_match"),
         state.get("duplicate_of"), _j(judge), _j(state.get("exec_result")), _j(state.get("fail_reasons", [])),
         tokens.get("input", 0), tokens.get("output", 0), tokens.get("cost_usd"), now()),
    )


def batch_slots(conn, batch_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT s.slot_no, s.bucket, s.topic, s.format, s.question_type, s.question_id, q.status
           FROM batch_slots s LEFT JOIN questions q ON q.question_id = s.question_id
           WHERE s.batch_id = ? ORDER BY s.slot_no""", (batch_id,)).fetchall()
    return [dict(r) for r in rows]


def passed_in_bucket(conn, bucket: str, exclude_qid: str | None = None) -> list[dict]:
    """dedupe 비교 대상: 같은 버킷의 passed 문제(본문, 인용)."""
    rows = conn.execute(
        "SELECT question_id, stem_en FROM questions WHERE bucket = ? AND status = 'passed' AND question_id IS NOT ?",
        (bucket, exclude_qid),
    ).fetchall()
    out = []
    for qid, stem in rows:
        quotes = conn.execute("SELECT quote FROM grounding_records WHERE question_id = ? ORDER BY idx", (qid,))
        out.append({"question_id": qid, "stem_en": stem, "grounding_records": [{"quote": q[0]} for q in quotes]})
    return out


def finish_batch(conn, batch_id: str, done: bool = True) -> None:
    """토큰 합계를 시도 행에서 다시 센다. 모든 슬롯이 끝났을 때만 `finished_at`을 채운다."""
    conn.execute(
        """UPDATE batches SET finished_at = ?,
               input_tokens = (SELECT COALESCE(SUM(v.input_tokens), 0) FROM verification_results v
                               JOIN questions q ON q.question_id = v.question_id WHERE q.batch_id = ?),
               output_tokens = (SELECT COALESCE(SUM(v.output_tokens), 0) FROM verification_results v
                                JOIN questions q ON q.question_id = v.question_id WHERE q.batch_id = ?),
               cost_usd = (SELECT CASE WHEN COUNT(*) > 0 AND COUNT(v.cost_usd) = COUNT(*) THEN SUM(v.cost_usd) END
                           FROM verification_results v
                           JOIN questions q ON q.question_id = v.question_id WHERE q.batch_id = ?)
           WHERE batch_id = ?""",
        (now() if done else None, batch_id, batch_id, batch_id, batch_id),
    )
