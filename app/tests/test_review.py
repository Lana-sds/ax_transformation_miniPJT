"""복습 큐(design.md 6.5, FR-5). 간격 계산과 상태 전이."""

import random

from quiz import review, sets
from quiz_helpers import add_attempt, add_review, add_set, make_pool, make_variant, review_row


def item(round_, due, state="pending", tag="reading"):
    return {"review_round": round_, "due_set_no": due, "state": state, "mistake_tag": tag}


# --- 간격 계산과 상태 전이(순수 함수) ---

def test_first_wrong_is_due_two_sets_later():
    assert review.transition(None, 4, correct=False, tag="reading") == item(1, 6)


def test_wrong_in_first_review_is_due_five_sets_later():
    assert review.transition(item(1, 6), 6, correct=False, tag="concept") == item(2, 11, tag="concept")


def test_carried_over_review_counts_from_the_set_it_was_served_in():
    """기한이 지나 다음 세트로 넘어간 항목은 실제로 낸 세트 번호 m에서 m+5를 센다."""
    assert review.transition(item(1, 6), 7, correct=False, tag="reading") == item(2, 12)


def test_wrong_in_second_review_retires():
    assert review.transition(item(2, 11, tag="concept"), 11, correct=False, tag="reading") == item(
        2, 11, "retired", "reading")


def test_correct_in_review_clears_both_rounds():
    assert review.transition(item(1, 6), 6, correct=True) == item(1, 6, "cleared")
    assert review.transition(item(2, 11), 12, correct=True) == item(2, 11, "cleared")


def test_correct_outside_review_changes_nothing():
    assert review.transition(None, 3, correct=True) is None
    assert review.transition(item(1, 9), 5, correct=True) == item(1, 9)
    assert review.transition(item(1, 6, "cleared"), 9, correct=True) == item(1, 6, "cleared")


def test_wrong_after_cleared_starts_over():
    assert review.transition(item(1, 6, "cleared"), 9, correct=False, tag="concept") == item(1, 11, tag="concept")


def test_retired_stays_retired():
    assert review.transition(item(2, 11, "retired"), 20, correct=False, tag="reading")["state"] == "retired"
    assert review.transition(item(2, 11, "retired"), 20, correct=True)["state"] == "retired"


# --- DB 반영 ---

def test_tag_queues_then_review_wrong_then_retire(tmp_db):
    pool = make_pool(tmp_db, 12)
    q = pool[0]
    review.record_tag(tmp_db, q, 1, "reading")
    assert review_row(tmp_db, q) == {"question_id": q, **item(1, 3)}
    review.record_answer(tmp_db, q, 3, correct=False)  # 오답 제출만으로는 바꾸지 않는다(태그가 필요하다)
    assert review_row(tmp_db, q)["review_round"] == 1
    review.record_tag(tmp_db, q, 3, "concept")
    assert review_row(tmp_db, q) == {"question_id": q, **item(2, 8, tag="concept")}
    review.record_tag(tmp_db, q, 8, "reading")
    assert review_row(tmp_db, q) == {"question_id": q, **item(2, 8, "retired", "reading")}


def test_correct_answer_in_review_clears(tmp_db):
    pool = make_pool(tmp_db, 12)
    add_review(tmp_db, pool[0], 1, 3)
    review.record_answer(tmp_db, pool[0], 3, correct=True)
    assert review_row(tmp_db, pool[0])["state"] == "cleared"


def test_retag_updates_tag_without_moving_the_item(tmp_db):
    pool = make_pool(tmp_db, 12)
    review.record_tag(tmp_db, pool[0], 1, "reading")
    review.retag(tmp_db, pool[0], "concept")
    assert review_row(tmp_db, pool[0]) == {"question_id": pool[0], **item(1, 3, tag="concept")}


def test_variant_result_updates_original_item(tmp_db):
    pool = make_pool(tmp_db, 12)
    variant = make_variant(tmp_db, pool[0], 1)
    add_review(tmp_db, pool[0], 1, 3, tag="concept")
    assert review.original_of(tmp_db, variant) == pool[0]
    review.record_tag(tmp_db, variant, 3, "concept")
    assert review_row(tmp_db, pool[0])["review_round"] == 2
    assert review_row(tmp_db, variant) is None


# --- 개념 실수 변형 대체 ---

def test_served_question_prefers_passed_variant_for_concept(tmp_db):
    pool = make_pool(tmp_db, 12)
    add_review(tmp_db, pool[0], 1, 3, tag="concept")
    add_review(tmp_db, pool[1], 1, 3, tag="concept")
    add_review(tmp_db, pool[2], 1, 3, tag="reading")
    add_review(tmp_db, pool[3], 1, 3, tag="concept")
    variant = make_variant(tmp_db, pool[0], 1)
    make_variant(tmp_db, pool[1], 2, status="dropped")
    make_variant(tmp_db, pool[2], 3)  # 독해 실수는 변형이 있어도 같은 문제
    rows = {r["question_id"]: r for r in tmp_db.execute("SELECT * FROM review_items")}
    assert review.served_question(tmp_db, rows[pool[0]]) == variant
    assert review.served_question(tmp_db, rows[pool[1]]) == pool[1]  # 통과한 변형 없음
    assert review.served_question(tmp_db, rows[pool[2]]) == pool[2]
    assert review.served_question(tmp_db, rows[pool[3]]) == pool[3]  # 변형 없음(T7.1 면제)


def test_set_composition_uses_variant_substitution(tmp_db):
    pool = make_pool(tmp_db, 20)
    s1 = add_set(tmp_db, 1, pool[:10])
    for q in pool[:10]:
        add_attempt(tmp_db, s1, q, correct=False, tag="concept")
    add_review(tmp_db, pool[0], 1, 3, tag="concept")
    add_review(tmp_db, pool[1], 1, 3, tag="concept")
    variant = make_variant(tmp_db, pool[0], 1)
    chosen = sets.compose(tmp_db, 3, random.Random(1))
    assert chosen[:2] == [variant, pool[1]]
    assert pool[0] not in chosen
