"""풀 스냅샷 고정과 현재 풀(design.md 5.2, 5.3, 6.3). 마지막으로 고정한 스냅샷이 현재 풀이다."""

import random

from conftest import make_question
from quiz import sets
from quiz.pool import current_pool, freeze
from quiz_helpers import make_pool, qid


def pool_items(conn, psid):
    return {r[0] for r in conn.execute(
        "SELECT question_id FROM pool_snapshot_items WHERE pool_snapshot_id = ?", (psid,))}


def test_refreeze_after_audit_failed_returns_to_older_snapshot(tmp_db):
    """A(10) 고정 → 1문제 추가 → B(11) 고정 → 그 문제 audit_failed → 다시 고정하면 A가 현재 풀이다(F-4)."""
    original = make_pool(tmp_db, 10)
    a = current_pool(tmp_db)
    extra = qid(11)
    make_question(tmp_db, extra)
    b, n = freeze(tmp_db)
    tmp_db.commit()
    assert b != a and n == 11 and current_pool(tmp_db) == b

    tmp_db.execute("UPDATE questions SET status = 'audit_failed' WHERE question_id = ?", (extra,))
    psid, n = freeze(tmp_db)
    tmp_db.commit()
    assert (psid, n) == (a, 10)
    assert current_pool(tmp_db) == psid
    assert extra not in pool_items(tmp_db, current_pool(tmp_db))

    made = sets.create(tmp_db, random.Random(1))
    assert extra not in made["question_ids"]
    assert set(made["question_ids"]) == set(original)
    assert tmp_db.execute("SELECT pool_snapshot_id FROM quiz_sets WHERE set_id = ?",
                          (made["set_id"],)).fetchone()[0] == a


def test_refreeze_of_current_pool_keeps_it(tmp_db):
    make_pool(tmp_db, 10)
    a = current_pool(tmp_db)
    created = tmp_db.execute("SELECT created_at FROM pool_snapshots WHERE pool_snapshot_id = ?", (a,)).fetchone()[0]
    assert freeze(tmp_db) == (a, 10)
    assert current_pool(tmp_db) == a
    assert tmp_db.execute("SELECT COUNT(*) FROM pool_snapshots").fetchone()[0] == 1
    assert tmp_db.execute("SELECT created_at FROM pool_snapshots WHERE pool_snapshot_id = ?",
                          (a,)).fetchone()[0] == created


def test_audit_failed_question_is_not_frozen(tmp_db):
    ids = make_pool(tmp_db, 11)
    tmp_db.execute("UPDATE questions SET status = 'audit_failed' WHERE question_id = ?", (ids[0],))
    psid, n = freeze(tmp_db)
    assert n == 10 and ids[0] not in pool_items(tmp_db, psid)
    assert current_pool(tmp_db) == psid
