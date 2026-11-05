"""복습 큐(design.md 6.5, FR-5). 간격은 세트 번호(`set_no`)로 센다.

- `set_no = n`에서 틀리면 `review_round=1, due_set_no=n+2`.
- 복습에서 맞히면 `cleared`. 1회차에서 틀리면 `review_round=2, due_set_no=m+5`(m은 그 문제를 낸 세트 번호).
  2회차에서 틀리면 `retired`.
- 복습 중인 문제는 `pending`이고 `due_set_no <= 세트 번호`인 항목이다. 기한이 지나 넘어간 항목도 낸 세트 번호로 센다.
- 오답 반영은 태그를 받을 때 한다(큐 항목의 `mistake_tag`가 필수다). 정답 반영은 답 제출 때 한다.
- 큐 항목의 `mistake_tag`는 마지막 태그로 바꾼다.
- `concept`이면 `variant_of = question_id`이고 `passed`인 변형 문제를 내고, 없으면 원래 문제를 낸다.
  변형 문제 풀이 결과는 원래 문제의 큐 항목에 반영한다. 변형 생성(T7.1)은 면제라 보통 원래 문제가 나간다.
"""

import sqlite3

FIRST_GAP = 2
SECOND_GAP = 5
_FIELDS = ("review_round", "due_set_no", "state", "mistake_tag")


def _is_reviewing(item: dict | None, set_no: int) -> bool:
    return item is not None and item["state"] == "pending" and item["due_set_no"] <= set_no


def transition(item: dict | None, set_no: int, correct: bool, tag: str | None = None) -> dict | None:
    """풀이 한 번을 반영한 큐 항목. 바뀌지 않으면 받은 값을 그대로 돌려준다. 오답이면 `tag`가 필요하다."""
    if correct:
        if _is_reviewing(item, set_no):
            return {**item, "state": "cleared"}
        return item
    if tag is None:
        raise ValueError("a wrong answer needs a mistake tag")
    if item is not None and item["state"] == "retired":
        return {**item, "mistake_tag": tag}
    if _is_reviewing(item, set_no):
        if item["review_round"] == 1:
            return {"review_round": 2, "due_set_no": set_no + SECOND_GAP, "state": "pending", "mistake_tag": tag}
        return {**item, "state": "retired", "mistake_tag": tag}
    if item is not None and item["state"] == "pending":
        # 기한 전 항목은 세트에 나오지 않는다. 태그만 바꾼다.
        return {**item, "mistake_tag": tag}
    return {"review_round": 1, "due_set_no": set_no + FIRST_GAP, "state": "pending", "mistake_tag": tag}


def original_of(conn: sqlite3.Connection, question_id: str) -> str:
    row = conn.execute("SELECT variant_of FROM questions WHERE question_id = ?", (question_id,)).fetchone()
    return row["variant_of"] if row and row["variant_of"] else question_id


def _load(conn: sqlite3.Connection, original: str) -> dict | None:
    row = conn.execute("SELECT * FROM review_items WHERE question_id = ?", (original,)).fetchone()
    return {k: row[k] for k in _FIELDS} if row else None


def _save(conn: sqlite3.Connection, original: str, before: dict | None, after: dict | None) -> None:
    if after is None or after == before:
        return
    conn.execute(
        """INSERT INTO review_items (question_id, review_round, due_set_no, state, mistake_tag)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT (question_id) DO UPDATE SET review_round = excluded.review_round,
               due_set_no = excluded.due_set_no, state = excluded.state, mistake_tag = excluded.mistake_tag""",
        (original, after["review_round"], after["due_set_no"], after["state"], after["mistake_tag"]),
    )


def record_answer(conn: sqlite3.Connection, question_id: str, set_no: int, correct: bool) -> None:
    """답 제출 때 부른다. 복습 중 정답이면 `cleared`. 오답은 태그를 받을 때 반영한다."""
    if not correct:
        return
    original = original_of(conn, question_id)
    before = _load(conn, original)
    _save(conn, original, before, transition(before, set_no, correct=True))


def record_tag(conn: sqlite3.Connection, question_id: str, set_no: int, tag: str) -> None:
    """오답 행에 처음 태그를 붙일 때 부른다. 큐에 넣거나 회차를 올리거나 `retired`로 바꾼다."""
    original = original_of(conn, question_id)
    before = _load(conn, original)
    _save(conn, original, before, transition(before, set_no, correct=False, tag=tag))


def retag(conn: sqlite3.Connection, question_id: str, tag: str) -> None:
    """이미 태그한 오답의 태그를 바꿀 때 부른다. 간격과 상태는 그대로 두고 태그만 바꾼다."""
    conn.execute("UPDATE review_items SET mistake_tag = ? WHERE question_id = ?", (tag, original_of(conn, question_id)))


def served_question(conn: sqlite3.Connection, item: sqlite3.Row | dict) -> str:
    """복습 항목으로 낼 문제 ID. 개념 실수이고 통과한 변형 문제가 있으면 변형 문제다."""
    if item["mistake_tag"] == "concept":
        row = conn.execute(
            "SELECT question_id FROM questions WHERE variant_of = ? AND status = 'passed' ORDER BY question_id LIMIT 1",
            (item["question_id"],),
        ).fetchone()
        if row:
            return row[0]
    return item["question_id"]
