"""FastAPI 서버(design.md 7.1). SQLite만 읽고 쓴다.

모델 호출, AWS 자격 증명, `.env` 로드가 없다(design.md 8.5). `quiz.llm`, `quiz.env`를 import하지 않는다.
세트 구성은 `quiz.sets`, 복습 큐는 `quiz.review`가 한다.

409 거절(design.md 8.6): 태그 없는 오답이 있을 때 다음 문제와 다음 세트, 정답 행 태그, 이미 푼 문제,
가장 최근 세트가 아닌 세트의 답 제출과 태그 변경, 10문제를 채우지 못하는 풀, 감사 표본 20문항을 채우지 못하는 풀.
409 응답의 `detail`은 `{"reason": ...}`이다.

API 명세는 `/openapi.json`(화면은 `/docs`)이다. 아래 응답 모델에서 나온다.
응답 모델은 정의에 없는 필드를 거절하므로, 서버가 모델과 다른 필드를 돌려주면 API 테스트가 실패한다.
"""

import json
import sqlite3
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from quiz import audit, db, grading, review, sets
from quiz.backup import backup
from quiz.migrate import apply_migrations, current_version, pending_migrations
from quiz.pool import current_pool
from quiz.store import now

DOCS_BASE = "https://docs.langchain.com"


@asynccontextmanager
async def lifespan(app: FastAPI):
    with db.connect() as conn:
        if pending_migrations(conn):  # 대기 중 마이그레이션이 있을 때만 백업한다(design.md 8.4)
            backup(db.db_path(), "migrate")
        apply_migrations(conn)
    yield


app = FastAPI(title="agent-dev-quiz", lifespan=lifespan)


# --- 응답 모델(API 명세). `web/src/api.ts`의 타입과 같은 모양이다. ---

class _Out(BaseModel):
    model_config = ConfigDict(extra="forbid")


MistakeTag = Literal["reading", "concept"]
AuditResult = Literal["pass", "fail"]


class HealthOut(_Out):
    ok: bool
    schema_version: int = Field(description="적용된 마이그레이션 번호")
    pool_snapshot_id: str | None = Field(description="현재 풀 스냅샷 ID. 풀이 없으면 null")


class ChoiceOut(_Out):
    id: str = Field(description="보기 ID(A, B, ...)")
    text: str | None = Field(None, description="글 보기")
    code: str | None = Field(None, description="코드 선택 문제의 코드 보기")


class SegmentOut(_Out):
    segment_id: str
    en: str = Field(description="문제 영문 구절")
    ko: str = Field(description="그 구절의 한국어 번역")


class GroundingOut(_Out):
    page: str = Field(description="문서 경로. API 레퍼런스는 전체 URL")
    url: str = Field(description="문서 URL")
    quote: str = Field(description="공식 문서 원문 인용")
    answer_basis: str = Field(description="인용이 정답을 뒷받침하는 이유(한국어)")


class PublicQuestionOut(_Out):
    """답 제출 전 공개 필드. 정답 키, 해설, 매핑, 근거, topic이 없다(FR-2.1)."""

    question_id: str
    bucket: str
    format: str = Field(description="single | multi | short | code")
    select_count: int | None = Field(description="복수 선택에서 고를 개수. 다른 형식은 null")
    stem_en: str = Field(description="영어 문제")
    choices: list[ChoiceOut] | None = Field(description="단답은 null")
    review: Literal["wrong", "seen"] | None = Field(
        description="앞 세트 기록. 오답이 있으면 wrong, 정답만 있으면 seen, 없으면 null")


class SetOut(_Out):
    set_id: str
    set_no: int
    questions: list[PublicQuestionOut]


class AnswerResultOut(_Out):
    attempt_id: int
    question_id: str
    answer: list[str] = Field(description="정규화한 제출 답")
    correct: bool
    answer_key: list[str]
    explanation_ko: str
    segments: list[SegmentOut]
    grounding: list[GroundingOut]
    doc_url: str | None = Field(description="코드 선택 문제의 문서 URL")
    mistake_tag: MistakeTag | None
    confused_segment_id: str | None


class SetDetailOut(SetOut):
    created_at: str
    completed: bool
    results: dict[str, AnswerResultOut] = Field(description="이미 푼 문제의 결과. 키는 question_id")
    untagged_attempt_ids: list[int] = Field(description="태그가 없는 오답 attempt_id")


class ReviewItemOut(_Out):
    review_round: int = Field(description="복습 회차(1, 2)")
    due_set_no: int = Field(description="복습 문제를 낼 세트 번호")
    state: Literal["pending", "cleared", "retired"]
    mistake_tag: MistakeTag


class TagResultOut(_Out):
    attempt_id: int
    question_id: str
    mistake_tag: MistakeTag
    confused_segment_id: str | None
    review: ReviewItemOut | None = Field(description="복습 큐 상태")


class AuditRecordOut(_Out):
    answer_key_error: bool
    quote_unsupported: bool
    mapping_unfaithful: bool
    note: str | None
    recorded_at: str


class AuditQuestionOut(PublicQuestionOut):
    answer_key: list[str]
    accepted_answers: list[str] | None = Field(description="단답 허용 답안")
    explanation_ko: str
    segments: list[SegmentOut]
    grounding: list[GroundingOut]
    doc_url: str | None


class AuditOut(_Out):
    audit_id: str
    pool_snapshot_id: str
    seed: str = Field(description="표본 시드. 풀 스냅샷 ID에서 파생한다")
    sample: list[str] = Field(description="표본 20문항의 question_id")
    created_at: str
    result: AuditResult | None = Field(description="20문항이 모두 기록되기 전에는 null")
    records: dict[str, AuditRecordOut] = Field(description="키는 question_id")
    questions: list[AuditQuestionOut]


class AuditRecordResultOut(_Out):
    audit_id: str
    question_id: str
    record: AuditRecordOut
    recorded: int = Field(description="기록한 문항 수")
    sample_size: int
    result: AuditResult | None


# --- 오류 응답(문서용). 실제 본문은 HTTPException이 만든다. ---

class ConflictDetail(BaseModel):
    """409 `detail`(design.md 8.6). `reason`에 따라 더하는 필드가 다르다."""

    reason: Literal["untagged_wrong", "set_closed", "correct_row", "already_answered", "pool_too_small", "no_pool"]
    set_id: str | None = Field(None, description="untagged_wrong, set_closed")
    attempt_ids: list[int] | None = Field(None, description="untagged_wrong")
    message: str | None = Field(None, description="pool_too_small, no_pool")


class ConflictOut(BaseModel):
    detail: ConflictDetail


class MessageOut(BaseModel):
    detail: str


CONFLICT = {409: {"model": ConflictOut, "description": "거절(design.md 8.6)"}}
NOT_FOUND = {404: {"model": MessageOut, "description": "대상이 없음"}}
BAD_REQUEST = {400: {"model": MessageOut, "description": "세트나 표본에 없는 문제"}}


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


# API 문서 화면(Scalar). 패키지 없이 CDN 스크립트로 `/openapi.json`을 그린다.
# 버전을 고정해 CDN 쪽 변경이 화면을 바꾸지 않게 한다. 인터넷이 없으면 빈 화면이다.
SCALAR_HTML = """<!doctype html>
<html>
  <head>
    <title>agent-dev-quiz - API Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <script id="api-reference" data-url="/openapi.json"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.76.4/dist/browser/standalone.js"></script>
  </body>
</html>
"""


@app.get("/scalar", response_class=HTMLResponse, include_in_schema=False)
def scalar_docs() -> str:
    return SCALAR_HTML


@app.get("/api/health", response_model=HealthOut)
def health() -> dict:
    with _conn() as conn:
        return {"ok": True, "schema_version": current_version(conn), "pool_snapshot_id": current_pool(conn)}


@app.post("/api/sets", response_model=SetOut, responses=CONFLICT)
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


@app.get("/api/sets/{set_id}", response_model=SetDetailOut, responses=NOT_FOUND)
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


@app.post("/api/sets/{set_id}/answers", response_model=AnswerResultOut,
          responses={**CONFLICT, **NOT_FOUND, **BAD_REQUEST})
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


@app.put("/api/attempts/{attempt_id}/tag", response_model=TagResultOut, responses={**CONFLICT, **NOT_FOUND})
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


@app.get("/api/audits/current", response_model=AuditOut, responses=NOT_FOUND)
def current_audit() -> dict:
    with _conn() as conn:
        a = audit.current(conn)
        if a is None:
            raise HTTPException(404, "no audit for current pool")
        return _audit_view(conn, a)


@app.post("/api/audits", response_model=AuditOut, responses=CONFLICT)
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


@app.put("/api/audits/{audit_id}/records/{question_id}", response_model=AuditRecordResultOut,
         responses={**NOT_FOUND, **BAD_REQUEST})
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
