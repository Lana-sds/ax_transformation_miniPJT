"""세트 구성(design.md 6.3, FR-1). 항상 10문제, 복습 최대 3개, 새 문제, 맞힌 문제 오래된 순, retired 제외."""

import json
import random

import pytest

from quiz import sets
from quiz_helpers import add_attempt, add_review, add_set, make_pool, make_variant, qid


def test_first_set_is_ten_new_questions(tmp_db):
    pool = make_pool(tmp_db, 15)
    chosen = sets.compose(tmp_db, 1, random.Random(1))
    assert len(chosen) == sets.SET_SIZE == 10
    assert len(set(chosen)) == 10
    assert set(chosen) <= set(pool)


def test_pool_smaller_than_ten_is_refused(tmp_db):
    """M0 임시 규칙(있는 만큼 낸다)을 없앴다. 10개를 못 채우면 세트를 만들지 않는다."""
    make_pool(tmp_db, 9)
    with pytest.raises(sets.PoolTooSmallError):
        sets.compose(tmp_db, 1, random.Random(1))


def test_more_than_three_due_reviews_serves_three_earliest(tmp_db):
    pool = make_pool(tmp_db, 20)
    s1 = add_set(tmp_db, 1, pool[:10])
    for q in pool[:10]:
        add_attempt(tmp_db, s1, q, correct=False, tag="reading", segment="s1")
    # 기한이 된 항목 5개(3번 세트 기준), 기한 전 1개
    for q, due in [(pool[0], 3), (pool[1], 3), (pool[2], 2), (pool[3], 3), (pool[4], 1), (pool[5], 4)]:
        add_review(tmp_db, q, 1, due)
    chosen = sets.compose(tmp_db, 3, random.Random(1))
    assert len(chosen) == 10
    assert chosen[:3] == [pool[4], pool[2], pool[0]]  # due 1, 2, 3(question_id 순)
    assert not {pool[1], pool[3], pool[5]} & set(chosen)  # 넘긴 항목, 기한 전 항목
    assert set(chosen[3:]) <= set(pool[10:])  # 나머지 7개는 새 문제


def test_fewer_reviews_are_filled_with_new_questions(tmp_db):
    pool = make_pool(tmp_db, 20)
    s1 = add_set(tmp_db, 1, pool[:10])
    for q in pool[:10]:
        add_attempt(tmp_db, s1, q, correct=q in pool[:2], tag=None if q in pool[:2] else "reading",
                    segment=None if q in pool[:2] else "s1")
    add_review(tmp_db, pool[2], 1, 3)
    chosen = sets.compose(tmp_db, 3, random.Random(1))
    assert chosen[0] == pool[2]
    assert len(chosen) == 10
    assert set(chosen[1:]) <= set(pool[10:])


def test_new_exhausted_fills_with_oldest_correct_and_skips_retired(tmp_db):
    pool = make_pool(tmp_db, 14)
    s1 = add_set(tmp_db, 1, pool[:12])
    # 12개 풀이. 9개 정답(시각 서로 다름), 3개 오답
    for i, q in enumerate(pool[:9]):
        add_attempt(tmp_db, s1, q, correct=True, ts=f"2026-11-05T00:00:{i:02d}Z")
    for q in pool[9:12]:
        add_attempt(tmp_db, s1, q, correct=False, ts="2026-11-05T00:00:00Z", tag="reading", segment="s1")
    add_review(tmp_db, pool[9], 1, 3)               # 기한 된 복습
    add_review(tmp_db, pool[10], 2, 9)              # 기한 전 복습: 큐에 있으므로 내지 않는다
    add_review(tmp_db, pool[11], 2, 1, "retired")   # retired: 다시 내지 않는다
    # retired 문제가 예전에 맞힌 적이 있어도 내지 않는다
    s2 = add_set(tmp_db, 2, [pool[11]])
    add_attempt(tmp_db, s2, pool[11], correct=True, ts="2026-11-04T00:00:00Z")
    chosen = sets.compose(tmp_db, 3, random.Random(1))
    assert len(chosen) == 10
    assert chosen[0] == pool[9]
    assert set(chosen[1:3]) == {pool[12], pool[13]}  # 남은 새 문제
    assert chosen[3:] == pool[:7]                    # 맞힌 문제, 마지막 풀이가 오래된 순
    assert pool[10] not in chosen and pool[11] not in chosen


def test_last_attempt_time_orders_correct_questions(tmp_db):
    pool = make_pool(tmp_db, 11)
    s1 = add_set(tmp_db, 1, pool)
    for i, q in enumerate(pool):
        add_attempt(tmp_db, s1, q, correct=True, ts=f"2026-11-05T00:00:{i:02d}Z")
    # 가장 오래 전에 푼 문제를 최근에 다시 풀면 맨 뒤로 간다
    s2 = add_set(tmp_db, 2, [pool[0]])
    add_attempt(tmp_db, s2, pool[0], correct=True, ts="2026-11-05T01:00:00Z")
    chosen = sets.compose(tmp_db, 3, random.Random(1))
    assert chosen == pool[1:11]


def test_review_outside_current_pool_is_skipped(tmp_db):
    """풀에서 빠진 문제(감사 실패 뒤 다시 고정한 풀)는 복습으로도 내지 않는다."""
    pool = make_pool(tmp_db, 12)
    s1 = add_set(tmp_db, 1, pool[:10])
    for q in pool[:10]:
        add_attempt(tmp_db, s1, q, correct=True)
    tmp_db.execute("UPDATE attempts SET correct = 0, mistake_tag = 'reading', confused_segment_id = 's1' "
                   "WHERE question_id = ?", (pool[0],))
    add_review(tmp_db, pool[0], 1, 3)
    tmp_db.execute("INSERT INTO pool_snapshots VALUES ('ps_other', '2099-01-01T00:00:00Z')")
    tmp_db.executemany("INSERT INTO pool_snapshot_items VALUES ('ps_other', ?)", [(q,) for q in pool[1:]])
    tmp_db.commit()
    chosen = sets.compose(tmp_db, 3, random.Random(1))
    assert pool[0] not in chosen
    assert len(chosen) == 10


def test_create_stores_set_with_next_number(tmp_db):
    make_pool(tmp_db, 12)
    first = sets.create(tmp_db, random.Random(1))
    second = sets.create(tmp_db, random.Random(2))
    assert (first["set_no"], second["set_no"]) == (1, 2)
    row = tmp_db.execute("SELECT * FROM quiz_sets WHERE set_id = ?", (second["set_id"],)).fetchone()
    assert json.loads(row["question_ids_json"]) == second["question_ids"]
    assert len(second["question_ids"]) == 10


def test_untagged_wrong_lists_only_wrong_rows_without_tag(tmp_db):
    pool = make_pool(tmp_db, 12)
    s1 = add_set(tmp_db, 1, pool[:10])
    add_attempt(tmp_db, s1, qid(1), correct=True)
    a2 = add_attempt(tmp_db, s1, qid(2), correct=False)
    add_attempt(tmp_db, s1, qid(3), correct=False, tag="concept")
    assert sets.untagged_wrong(tmp_db, s1) == [a2]


def test_review_status_from_earlier_sets(tmp_db):
    """T4.8: 이전 세트 기록에 오답이 있으면 wrong, 정답만 있으면 seen, 없으면 None. 변형은 원래 문제로 센다."""
    ids = make_pool(tmp_db, 12)
    variant = make_variant(tmp_db, ids[3], 1)
    s1 = add_set(tmp_db, 1, ids[:10])
    add_attempt(tmp_db, s1, ids[0], correct=False, tag="concept")
    add_attempt(tmp_db, s1, ids[1], correct=True)
    add_attempt(tmp_db, s1, ids[2], correct=False, tag="concept")
    add_attempt(tmp_db, s1, ids[3], correct=False, tag="concept")
    s2 = add_set(tmp_db, 2, [ids[2]])
    add_attempt(tmp_db, s2, ids[2], correct=True)
    s3 = add_set(tmp_db, 3, [ids[0], ids[1], ids[2], variant, ids[10]])
    add_attempt(tmp_db, s3, ids[10], correct=False, tag="concept")  # 이번 세트 기록은 세지 않는다

    status = sets.review_status(tmp_db, 3, [ids[0], ids[1], ids[2], variant, ids[10]])
    assert status == {ids[0]: "wrong", ids[1]: "seen", ids[2]: "wrong", variant: "wrong", ids[10]: None}
    assert sets.review_status(tmp_db, 1, ids[:2]) == {ids[0]: None, ids[1]: None}
