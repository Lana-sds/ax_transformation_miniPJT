from quiz.db import connect
from quiz.migrate import apply_migrations, current_version

TABLES = {
    "schema_version", "batches", "batch_slots", "questions", "grounding_records",
    "verification_results", "pool_snapshots", "pool_snapshot_items", "quiz_sets",
    "attempts", "review_items", "audits", "audit_records",
}


def test_migrate_creates_all_tables_and_is_idempotent(tmp_path):
    conn = connect(tmp_path / "t.db")
    assert apply_migrations(conn) == [1, 2]
    assert apply_migrations(conn) == []
    assert current_version(conn) == 2
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert TABLES <= names
