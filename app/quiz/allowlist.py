"""`packs/langchain/allowlist.yaml` 만들기와 읽기(design.md 4.3, GR-2.3).

파이프라인은 이 파일에 있는 스냅샷만 읽는다. 스냅샷 해시가 다르면 멈춘다.

- `parse_page_table`: page-allowlist.md 표를 행 목록으로 바꾼다. `없음` 행(경로 `-`)은 뺀다.
- `snapshot-manifest.yaml`: `snapshot fetch`가 서버 sha256과 대조한 값을 적는다. `build`의 기대 해시다.
- `build`: 행마다 스냅샷 파일 해시를 manifest와 대조하고 `snapshot`, `sha256`, `fetched_at`을 붙인다.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

from quiz.db import REPO_ROOT
from quiz.snapshots import SNAPSHOT_DIR, file_sha256

PACK_DIR = REPO_ROOT / "packs" / "langchain"
ALLOWLIST_PATH = PACK_DIR / "allowlist.yaml"
MANIFEST_PATH = PACK_DIR / "snapshot-manifest.yaml"
PAGE_ALLOWLIST_MD = REPO_ROOT / "docs" / "02-spec-design" / "output" / "page-allowlist.md"

# page-allowlist.md 버킷 절 제목(괄호 앞) -> 버킷 식별자(design.md 5.2)
BUCKETS = {
    "RAG": "rag",
    "LangGraph 기초": "langgraph_basics",
    "Tool · MCP": "tool_mcp",
    "미들웨어 · HITL · 가드레일": "middleware_hitl_guardrails",
    "멀티 에이전트": "multi_agent",
    "운영 품질": "ops_quality",
}

_HEADING = re.compile(r"^##\s+(.+?)\s*(\(.*\))?\s*$")


class AllowlistError(RuntimeError):
    pass


def parse_page_table(text: str) -> list[dict]:
    rows: list[dict] = []
    bucket: str | None = None
    for line in text.splitlines():
        if m := _HEADING.match(line):
            bucket = BUCKETS.get(m.group(1).strip())
            continue
        if bucket is None or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].isdigit():
            continue  # 머리 줄, 구분 줄
        no, topic, path, kind, status = cells[:5]
        path = path.strip("`")
        if status == "없음" or path == "-":
            continue
        rows.append({"bucket": bucket, "topic_no": int(no), "topic": topic, "path": path,
                     "kind": kind, "status": status})
    return rows


def snapshot_for(path: str, kind: str) -> str:
    """docs: 경로의 `/`를 `__`로(.mdx). api-ref: `reference__` + URL 경로(.md, `get_symbol` 출력)."""
    if kind == "api-ref":
        return "reference__" + urlparse(path).path.strip("/").replace("/", "__") + ".md"
    return path.strip("/").replace("/", "__") + ".mdx"


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("snapshots", {})


def record_fetch(path: Path, snapshot: str, sha256: str, fetched_at: str) -> None:
    """서버 해시와 대조를 마친 스냅샷 하나를 manifest에 적는다."""
    data = load_manifest(path)
    data[snapshot] = {"sha256": sha256, "fetched_at": fetched_at}
    header = "# 스냅샷 기대 해시. `quiz snapshot fetch`가 서버 sha256 대조 뒤 쓴다. 손으로 고치지 않는다.\n"
    path.write_text(header + yaml.safe_dump({"snapshots": dict(sorted(data.items()))}, allow_unicode=True,
                                            sort_keys=False), encoding="utf-8")


def build(rows: list[dict], manifest_path: Path = MANIFEST_PATH, snapshot_dir: Path = SNAPSHOT_DIR,
          allow_missing: bool = False) -> list[dict]:
    manifest = load_manifest(manifest_path)
    out, missing = [], []
    for row in rows:
        name = snapshot_for(row["path"], row["kind"])
        entry = manifest.get(name)
        file = snapshot_dir / name
        if entry is None or not file.exists():
            missing.append(name)
            out.append({**row, "snapshot": None, "sha256": None, "fetched_at": None})
            continue
        actual = file_sha256(file)
        if actual != entry["sha256"]:
            raise AllowlistError(f"snapshot hash mismatch: {name} {actual} != {entry['sha256']}")
        out.append({**row, "snapshot": name, "sha256": actual, "fetched_at": str(entry["fetched_at"])})
    if missing and not allow_missing:
        raise AllowlistError(f"snapshot missing ({len(set(missing))}): " + ", ".join(sorted(set(missing))))
    return out


def write_yaml(rows: list[dict], path: Path = ALLOWLIST_PATH) -> None:
    header = ("# 허용 목록(design.md 4.3, GR-2). `quiz allowlist build`가 "
              "docs/02-spec-design/output/page-allowlist.md 표에서 만든다. 손으로 고치지 않는다.\n")
    path.write_text(header + yaml.safe_dump({"pages": rows}, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")


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
