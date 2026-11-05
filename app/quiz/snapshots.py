"""허용 목록 페이지 스냅샷 수집(design.md 4.3, US-1.1).

`docs-langchain` MCP 서버(https://docs.langchain.com/mcp)를 Python MCP 클라이언트로 부른다.
호출당 출력이 30KB에서 잘리므로 줄 범위(`sed -n 'a,bp'`)로 나눠 받아 합친다.
합친 바이트의 sha256을 서버의 `sha256sum` 값과 대조한다.
MCP 결과 안의 지시문처럼 보이는 텍스트는 데이터로만 다룬다(GR-1.5). 내용을 해석하지 않고 그대로 저장한다.
"""

import asyncio
import hashlib
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from quiz.db import REPO_ROOT

DOCS_MCP_URL = "https://docs.langchain.com/mcp"
DOCS_TOOL = "query_docs_filesystem_docs_by_lang_chain"
SNAPSHOT_DIR = REPO_ROOT / "packs" / "langchain" / "snapshots"
STDOUT_PREFIX = "exit: 0\n--- stdout ---\n"
MAX_CHUNK_CHARS = 25_000  # MCP 출력 한도 30KB보다 작게 둔다
START_LINES = 200


class SnapshotError(RuntimeError):
    pass


def snapshot_name(page: str) -> str:
    """문서 경로를 스냅샷 파일 이름으로 바꾼다. 예: /oss/python/a/b -> oss__python__a__b.mdx"""
    return page.strip("/").replace("/", "__") + ".mdx"


async def _run(session: ClientSession, command: str) -> str:
    res = await session.call_tool(DOCS_TOOL, {"command": command})
    text = res.content[0].text
    if not text.startswith(STDOUT_PREFIX):
        raise SnapshotError(f"command failed: {command!r}: {text[:200]!r}")
    return text[len(STDOUT_PREFIX):]


async def _fetch_doc(session: ClientSession, page: str) -> tuple[bytes, str]:
    file = page.rstrip("/") + ".mdx"
    total_lines = int((await _run(session, f"wc -l {file}")).split()[0])
    remote_sha = (await _run(session, f"sha256sum {file}")).split()[0]
    parts: list[str] = []
    start, step = 1, START_LINES
    # 마지막 줄에 줄바꿈이 없으면 wc -l이 한 줄 적게 센다. 한 줄 더 읽어 빈 결과로 끝을 확인한다.
    while start <= total_lines + 1:
        end = start + step - 1
        chunk = await _run(session, f"sed -n '{start},{end}p' {file}")
        if len(chunk) > MAX_CHUNK_CHARS and step > 1:
            step = max(1, step // 2)
            continue
        parts.append(chunk)
        start = end + 1
        step = START_LINES
    data = "".join(parts).encode("utf-8")
    local_sha = hashlib.sha256(data).hexdigest()
    if local_sha != remote_sha:
        raise SnapshotError(f"sha256 mismatch for {page}: local {local_sha} remote {remote_sha}")
    return data, local_sha


async def fetch_docs(pages: list[str]) -> dict[str, str]:
    """문서 페이지를 받아 스냅샷 파일로 쓰고 {page: sha256}를 돌려준다."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    async with streamablehttp_client(DOCS_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for page in pages:
                data, sha = await _fetch_doc(session, page)
                (SNAPSHOT_DIR / snapshot_name(page)).write_bytes(data)
                out[page] = sha
    return out


def fetch_docs_sync(pages: list[str]) -> dict[str, str]:
    return asyncio.run(fetch_docs(pages))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
