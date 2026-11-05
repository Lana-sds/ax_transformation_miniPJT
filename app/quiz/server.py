"""FastAPI 서버(design.md 7.1). SQLite만 읽고 쓴다.

모델 호출, AWS 자격 증명, `.env` 로드가 없다(design.md 8.5). `quiz.llm`, `quiz.env`를 import하지 않는다.
세트 구성은 `quiz.sets`, 복습 큐는 `quiz.review`가 한다.

409 거절(design.md 8.6): 태그 없는 오답이 있을 때 다음 문제와 다음 세트, 정답 행 태그, 이미 푼 문제,
가장 최근 세트가 아닌 세트의 답 제출과 태그 변경, 10문제를 채우지 못하는 풀, 감사 표본 20문항을 채우지 못하는 풀.
409 응답의 `detail`은 `{"reason": ...}`이다.
"""

import json
import sqlite3
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from quiz import audit, db, grading, review, sets
from quiz.migrate import apply_migrations, current_version
from quiz.pool import current_pool
from quiz.store import now

DOCS_BASE = "https://docs.langchain.com"


@asynccontextmanager
async def lifespan(app: FastAPI):
    with db.connect() as conn:
        apply_migrations(conn)
    yield


app = FastAPI(title="agent-dev-quiz", lifespan=lifespan)


def _conn() -> sqlite3.Connection:
    return db.connect()


def _doc_url(page: str) -> str:
    return page if page.startswith("http") else DOCS_BASE + page


def _public_question(row: sqlite3.Row, review_state: str | None = None) -> dict:
    """답 제출 전 공개 필드. 정답 키, 해설, 매핑, 근거, topic을 넣지 않는다(FR-2.1).

    review는 이전 세트 기록이다(`sets.review_status`, T4.8).
    """
    return {
        "question_id": row["question_id"],
        "bucket": row["bucket"],
        "format": row["format"],
        "select_count": row["select_count"],
        "stem_en": row["stem_en"],
        "choices": json.loads(row["choices_json"]) if row["choices_json"] else None,
        "review": review_state,
    }


def _result(conn: sqlite3.Connection, row: sqlite3.Row, attempt: sqlite3.Row) -> dict:
    grounding = [
        {"page": g["page"], "url": _doc_url(g["page"]), "quote": g["quote"], "answer_basis": g["answer_basis"]}
        for g in conn.execute(
            "SELECT page, quote, answer_basis FROM grounding_records WHERE question_id = ? ORDER BY idx",
            (row["question_id"],),
        )
    ]
    return {
        "attempt_id": attempt["attempt_id"],
        "question_id": row["question_id"],
        "answer": json.loads(attempt["answer"]),
        "correct": bool(attempt["correct"]),
        "answer_key": json.loads(row["answer_key_json"]),
        "explanation_ko": row["explanation_ko"],
        "segments": json.loads(row["segments_json"]),
        "grounding": grounding,
        "doc_url": row["doc_url"],
        "mistake_tag": attempt["mistake_tag"],
        "confused_segment_id": attempt["confused_segment_id"],
    }


def _conflict(reason: str, **extra) -> HTTPException:
    return HTTPException(409, {"reason": reason, **extra})


def _require_tagged(conn: sqlite3.Connection, set_id: str) -> None:
    pending = sets.untagged_wrong(conn, set_id)
    if pending:
        raise _conflict("untagged_wrong", set_id=set_id, attempt_ids=pending)


def _require_latest(conn: sqlite3.Connection, qset: sqlite3.Row) -> None:
    latest = sets.latest_set(conn)
    if latest is None or latest["set_no"] != qset["set_no"]:
        raise _conflict("set_closed", set_id=qset["set_id"])


def _questions(conn: sqlite3.Connection, ids: list[str]) -> dict[str, sqlite3.Row]:
    return {r["question_id"]: r for r in conn.execute(
        f"SELECT * FROM questions WHERE question_id IN ({','.join('?' * len(ids))})", ids
    )}


@app.get("/api/health")
def health() -> dict:
    with _conn() as conn:
        return {"ok": True, "schema_version": current_version(conn), "pool_snapshot_id": current_pool(conn)}


@app.post("/api/sets")
def create_set() -> dict:
    with _conn() as conn:
        prev = sets.latest_set(conn)
        if prev is not None:
            _require_tagged(conn, prev["set_id"])
        try:
            created = sets.create(conn)
        except sets.NoPoolError as exc:
            raise _conflict("no_pool", message=str(exc))
        except sets.PoolTooSmallError as exc:
            raise _conflict("pool_too_small", message=str(exc))
        chosen = created["question_ids"]
        rows = _questions(conn, chosen)
        status = sets.review_status(conn, created["set_no"], chosen)
        return {"set_id": created["set_id"], "set_no": created["set_no"],
                "questions": [_public_question(rows[q], status[q]) for q in chosen]}


@app.get("/api/sets/{set_id}")
def get_set(set_id: str) -> dict:
    """세트와 이미 푼 문제의 결과. 새로고침 뒤 이어 풀기(FR-8.1)."""
    with _conn() as conn:
        qset = conn.execute("SELECT * FROM quiz_sets WHERE set_id = ?", (set_id,)).fetchone()
        if qset is None:
            raise HTTPException(404, "set not found")
        ids = json.loads(qset["question_ids_json"])
        rows = _questions(conn, ids)
        status = sets.review_status(conn, qset["set_no"], ids)
        results = {
            a["question_id"]: _result(conn, rows[a["question_id"]], a)
            for a in conn.execute("SELECT * FROM attempts WHERE set_id = ? ORDER BY attempt_id", (set_id,))
        }
        return {
            "set_id": qset["set_id"],
            "set_no": qset["set_no"],
            "created_at": qset["created_at"],
            "completed": qset["completed_at"] is not None,
            "questions": [_public_question(rows[q], status[q]) for q in ids],
            "results": results,
            "untagged_attempt_ids": sets.untagged_wrong(conn, set_id),
        }


class AnswerIn(BaseModel):
    question_id: str
    answer: str | list[str]


@app.post("/api/sets/{set_id}/answers")
def submit_answer(set_id: str, body: AnswerIn) -> dict:
    with _conn() as conn:
        qset = conn.execute("SELECT * FROM quiz_sets WHERE set_id = ?", (set_id,)).fetchone()
        if qset is None:
            raise HTTPException(404, "set not found")
        ids = json.loads(qset["question_ids_json"])
        if body.question_id not in ids:
            raise HTTPException(400, "question not in set")
        if conn.execute("SELECT 1 FROM attempts WHERE set_id = ? AND question_id = ?",
                        (set_id, body.question_id)).fetchone():
            raise _conflict("already_answered")
        _require_latest(conn, qset)
        _require_tagged(conn, set_id)
        row = conn.execute("SELECT * FROM questions WHERE question_id = ?", (body.question_id,)).fetchone()
        answer = grading.normalize_answer(body.answer)
        answer_key = json.loads(row["answer_key_json"])
        # 단답은 허용 답안과 비교한다(FR-3.2). 허용 답안이 없으면 정답 키를 쓴다.
        accepted = json.loads(row["accepted_answers_json"]) if row["accepted_answers_json"] else answer_key
        correct = grading.grade(row["format"], answer, {"answer_key": answer_key, "accepted_answers": accepted})
        cur = conn.execute(
            """INSERT INTO attempts (question_id, set_id, ts, answer, correct, schema_version)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (body.question_id, set_id, now(), json.dumps(answer), int(correct), current_version(conn)),
        )
        review.record_answer(conn, body.question_id, qset["set_no"], correct)
        answered = conn.execute("SELECT COUNT(*) FROM attempts WHERE set_id = ?", (set_id,)).fetchone()[0]
        if answered == len(ids):
            conn.execute("UPDATE quiz_sets SET completed_at = ? WHERE set_id = ?", (now(), set_id))
        attempt = conn.execute("SELECT * FROM attempts WHERE attempt_id = ?", (cur.lastrowid,)).fetchone()
        return _result(conn, row, attempt)


class TagIn(BaseModel):
    mistake_tag: Literal["reading", "concept"]
    confused_segment_id: str | None = None


@app.put("/api/attempts/{attempt_id}/tag")
def tag_attempt(attempt_id: int, body: TagIn) -> dict:
    """오답 행에만 태그를 붙인다(FR-4). 처음 태그하면 복습 큐를 갱신하고, 다시 태그하면 태그만 바꾼다."""
    with _conn() as conn:
        attempt = conn.execute("SELECT * FROM attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
        if attempt is None:
            raise HTTPException(404, "attempt not found")
        if attempt["correct"]:
            raise _conflict("correct_row")
        qset = conn.execute("SELECT * FROM quiz_sets WHERE set_id = ?", (attempt["set_id"],)).fetchone()
        _require_latest(conn, qset)
        question = conn.execute("SELECT * FROM questions WHERE question_id = ?", (attempt["question_id"],)).fetchone()
        segment = None
        if body.mistake_tag == "reading":
            known = {s["segment_id"] for s in json.loads(question["segments_json"])}
            if body.confused_segment_id not in known:
                raise HTTPException(422, "reading needs confused_segment_id from the question segments")
            segment = body.confused_segment_id
        first = attempt["mistake_tag"] is None
        conn.execute("UPDATE attempts SET mistake_tag = ?, confused_segment_id = ? WHERE attempt_id = ?",
                     (body.mistake_tag, segment, attempt_id))
        if first:
            review.record_tag(conn, attempt["question_id"], qset["set_no"], body.mistake_tag)
        else:
            review.retag(conn, attempt["question_id"], body.mistake_tag)
        item = conn.execute(
            "SELECT review_round, due_set_no, state, mistake_tag FROM review_items WHERE question_id = ?",
            (review.original_of(conn, attempt["question_id"]),),
        ).fetchone()
        return {
            "attempt_id": attempt_id,
            "question_id": attempt["question_id"],
            "mistake_tag": body.mistake_tag,
            "confused_segment_id": segment,
            "review": dict(item) if item else None,
        }


def _audit_view(conn: sqlite3.Connection, a: dict) -> dict:
    """감사 화면용. 표본 문제마다 정답 키, 해설, 매핑, 근거를 넣는다(design.md 7.1)."""
    rows = _questions(conn, a["sample"])
    questions = []
    for qid in a["sample"]:
        row = rows[qid]
        grounding = [
            {"page": g["page"], "url": _doc_url(g["page"]), "quote": g["quote"], "answer_basis": g["answer_basis"]}
            for g in conn.execute(
                "SELECT page, quote, answer_basis FROM grounding_records WHERE question_id = ? ORDER BY idx", (qid,))
        ]
        questions.append({
            **_public_question(row),
            "answer_key": json.loads(row["answer_key_json"]),
            "accepted_answers": json.loads(row["accepted_answers_json"]) if row["accepted_answers_json"] else None,
            "explanation_ko": row["explanation_ko"],
            "segments": json.loads(row["segments_json"]),
            "grounding": grounding,
            "doc_url": row["doc_url"],
        })
    return {**a, "questions": questions}


@app.get("/api/audits/current")
def current_audit() -> dict:
    with _conn() as conn:
        a = audit.current(conn)
        if a is None:
            raise HTTPException(404, "no audit for current pool")
        return _audit_view(conn, a)


@app.post("/api/audits")
def create_audit() -> dict:
    """현재 풀 스냅샷에서 시드와 표본을 만든다. 같은 스냅샷이면 기존 감사를 돌려준다(FR-9.1)."""
    with _conn() as conn:
        try:
            a = audit.create(conn)
        except audit.NoPool:
            raise _conflict("no_pool")
        except audit.PoolTooSmall as exc:
            raise _conflict("pool_too_small", message=f"pool has {exc.args[0]} questions, audit needs {audit.SAMPLE_SIZE}")
        return _audit_view(conn, a)


class AuditRecordIn(BaseModel):
    answer_key_error: bool
    quote_unsupported: bool
    mapping_unfaithful: bool
    note: str | None = None


@app.put("/api/audits/{audit_id}/records/{question_id}")
def record_audit(audit_id: str, question_id: str, body: AuditRecordIn) -> dict:
    """문항별 감사 결과 저장. 표본 20문항이 모두 차면 `result`를 계산한다(FR-9.2)."""
    with _conn() as conn:
        try:
            a = audit.record(conn, audit_id, question_id, answer_key_error=body.answer_key_error,
                             quote_unsupported=body.quote_unsupported,
                             mapping_unfaithful=body.mapping_unfaithful, note=body.note)
        except audit.AuditNotFound:
            raise HTTPException(404, "audit not found")
        except audit.NotInSample:
            raise HTTPException(400, "question not in audit sample")
        return {"audit_id": audit_id, "question_id": question_id, "record": a["records"][question_id],
                "recorded": len(a["records"]), "sample_size": len(a["sample"]), "result": a["result"]}
