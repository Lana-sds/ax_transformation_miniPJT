"""FastAPI 서버(design.md 7.1). SQLite만 읽고 쓴다.

모델 호출, AWS 자격 증명, `.env` 로드가 없다(design.md 8.5). `quiz.llm`, `quiz.env`를 import하지 않는다.
세트 구성은 `quiz.sets`가 한다. 10문제를 채우지 못하면 409다.
"""

import json
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from quiz import db, grading, sets
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


def _public_question(row: sqlite3.Row) -> dict:
    """답 제출 전 공개 필드. 정답 키, 해설, 매핑, 근거를 넣지 않는다(FR-2.1)."""
    return {
        "question_id": row["question_id"],
        "bucket": row["bucket"],
        "format": row["format"],
        "select_count": row["select_count"],
        "stem_en": row["stem_en"],
        "choices": json.loads(row["choices_json"]) if row["choices_json"] else None,
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
    }


@app.get("/api/health")
def health() -> dict:
    with _conn() as conn:
        return {"ok": True, "schema_version": current_version(conn), "pool_snapshot_id": current_pool(conn)}


@app.post("/api/sets")
def create_set() -> dict:
    with _conn() as conn:
        try:
            created = sets.create(conn)
        except (sets.NoPoolError, sets.PoolTooSmallError) as exc:
            raise HTTPException(409, str(exc))
        chosen = created["question_ids"]
        rows = {r["question_id"]: r for r in conn.execute(
            f"SELECT * FROM questions WHERE question_id IN ({','.join('?' * len(chosen))})", chosen
        )}
        return {"set_id": created["set_id"], "set_no": created["set_no"],
                "questions": [_public_question(rows[q]) for q in chosen]}


class AnswerIn(BaseModel):
    question_id: str
    answer: str | list[str]


@app.post("/api/sets/{set_id}/answers")
def submit_answer(set_id: str, body: AnswerIn) -> dict:
    with _conn() as conn:
        qset = conn.execute("SELECT * FROM quiz_sets WHERE set_id = ?", (set_id,)).fetchone()
        if qset is None:
            raise HTTPException(404, "set not found")
        if body.question_id not in json.loads(qset["question_ids_json"]):
            raise HTTPException(400, "question not in set")
        row = conn.execute("SELECT * FROM questions WHERE question_id = ?", (body.question_id,)).fetchone()
        answer = grading.normalize_answer(body.answer)
        correct = grading.grade(row["format"], answer, {"answer_key": json.loads(row["answer_key_json"])})
        try:
            cur = conn.execute(
                """INSERT INTO attempts (question_id, set_id, ts, answer, correct, schema_version)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (body.question_id, set_id, now(), json.dumps(answer), int(correct), current_version(conn)),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "already answered")
        attempt = conn.execute("SELECT * FROM attempts WHERE attempt_id = ?", (cur.lastrowid,)).fetchone()
        return _result(conn, row, attempt)
