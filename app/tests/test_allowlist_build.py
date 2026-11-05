import hashlib

import pytest
import yaml

from quiz import allowlist
from quiz.allowlist import AllowlistError

PAGE_TABLE = """# 허용 목록

## RAG (day2)

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 1 | 문서 로드 | `/oss/python/a` | docs | 확인 | "x" |
| 7 | 재랭킹 | https://reference.langchain.com/python/pkg/mod/Cls | api-ref | 확인 | y |

## Tool · MCP (day4)

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 3 | FastMCP 서버 | - | - | 없음 | 없다 |
| 4 | MCP 클라이언트 | `/oss/python/b` | docs | 근접 | z |

## 요약

| 버킷 | 주제 | 확인 | 근접만 | 없음 |
| --- | --- | --- | --- | --- |
| RAG | 7 | 7 | 0 | 0 |
"""


def test_parse_page_table_maps_buckets_and_skips_none_rows():
    rows = allowlist.parse_page_table(PAGE_TABLE)
    assert [(r["bucket"], r["topic_no"], r["path"], r["kind"], r["status"]) for r in rows] == [
        ("rag", 1, "/oss/python/a", "docs", "확인"),
        ("rag", 7, "https://reference.langchain.com/python/pkg/mod/Cls", "api-ref", "확인"),
        ("tool_mcp", 4, "/oss/python/b", "docs", "근접"),
    ]
    assert rows[0]["topic"] == "문서 로드"


def test_parse_real_page_allowlist_has_six_buckets():
    rows = allowlist.parse_page_table(allowlist.PAGE_ALLOWLIST_MD.read_text(encoding="utf-8"))
    assert {r["bucket"] for r in rows} == set(allowlist.BUCKETS.values())
    assert all(r["path"] != "-" for r in rows)


def test_snapshot_names():
    assert allowlist.snapshot_for("/oss/python/a/b", "docs") == "oss__python__a__b.mdx"
    assert (
        allowlist.snapshot_for("https://reference.langchain.com/python/pkg/mod/Cls", "api-ref")
        == "reference__python__pkg__mod__Cls.md"
    )


def _setup(tmp_path, content=b"hello snapshot\n"):
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    name = "oss__python__a.mdx"
    (snap_dir / name).write_bytes(content)
    manifest = tmp_path / "manifest.yaml"
    allowlist.record_fetch(manifest, name, hashlib.sha256(content).hexdigest(), "2026-11-05")
    rows = [{"bucket": "rag", "topic_no": 1, "topic": "t", "path": "/oss/python/a", "kind": "docs", "status": "확인"}]
    return snap_dir, manifest, rows, name


def test_build_writes_snapshot_sha_and_fetched_at(tmp_path):
    snap_dir, manifest, rows, name = _setup(tmp_path)
    out = allowlist.build(rows, manifest, snap_dir)
    assert out[0]["snapshot"] == name
    assert out[0]["sha256"] == hashlib.sha256(b"hello snapshot\n").hexdigest()
    assert out[0]["fetched_at"] == "2026-11-05"


def test_build_stops_on_one_byte_change_and_passes_after_revert(tmp_path):
    snap_dir, manifest, rows, name = _setup(tmp_path)
    (snap_dir / name).write_bytes(b"hello snapshot!")
    with pytest.raises(AllowlistError, match="hash mismatch"):
        allowlist.build(rows, manifest, snap_dir)
    (snap_dir / name).write_bytes(b"hello snapshot\n")
    allowlist.build(rows, manifest, snap_dir)


def test_build_missing_snapshot_errors_unless_allowed(tmp_path):
    snap_dir, manifest, rows, _ = _setup(tmp_path)
    rows = rows + [{"bucket": "rag", "topic_no": 2, "topic": "u", "path": "/oss/python/c", "kind": "docs", "status": "확인"}]
    with pytest.raises(AllowlistError, match="missing"):
        allowlist.build(rows, manifest, snap_dir)
    out = allowlist.build(rows, manifest, snap_dir, allow_missing=True)
    assert out[1]["snapshot"] is None
    assert allowlist.allowed_pages(out) == {"/oss/python/a"}


def test_write_and_load_roundtrip(tmp_path):
    snap_dir, manifest, rows, _ = _setup(tmp_path)
    path = tmp_path / "allowlist.yaml"
    allowlist.write_yaml(allowlist.build(rows, manifest, snap_dir), path)
    loaded = allowlist.load_rows(path)
    assert loaded[0]["path"] == "/oss/python/a"
    assert yaml.safe_load(path.read_text(encoding="utf-8"))["pages"][0]["sha256"]
