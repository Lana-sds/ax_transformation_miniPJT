"""`packs/langchain/allowlist.yaml` 읽기(design.md 4.3, GR-2.3).

파이프라인은 이 파일에 있는 스냅샷만 읽는다. 스냅샷 해시가 다르면 멈춘다.
"""

from pathlib import Path

import yaml

from quiz.db import REPO_ROOT
from quiz.snapshots import SNAPSHOT_DIR, file_sha256

ALLOWLIST_PATH = REPO_ROOT / "packs" / "langchain" / "allowlist.yaml"


class AllowlistError(RuntimeError):
    pass


def load_rows(path: Path = ALLOWLIST_PATH) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("pages", [])


def verify(rows: list[dict], snapshot_dir: Path = SNAPSHOT_DIR) -> None:
    for row in rows:
        if not row.get("snapshot"):
            continue
        actual = file_sha256(snapshot_dir / row["snapshot"])
        if actual != row["sha256"]:
            raise AllowlistError(f"snapshot hash mismatch: {row['snapshot']} {actual} != {row['sha256']}")


def allowed_pages(rows: list[dict]) -> set[str]:
    return {row["path"] for row in rows if row.get("snapshot")}


def read_snapshot(row: dict, snapshot_dir: Path = SNAPSHOT_DIR) -> str:
    return (snapshot_dir / row["snapshot"]).read_bytes().decode("utf-8")
