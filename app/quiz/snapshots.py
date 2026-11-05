"""허용 목록 페이지 스냅샷 수집(design.md 4.3, US-1.1).

`docs-langchain` MCP 서버(https://docs.langchain.com/mcp)를 Python MCP 클라이언트로 부른다.
호출당 출력이 30KB에서 잘리므로 줄 범위(`sed -n 'a,bp'`)로 나눠 받아 합친다.
합친 바이트의 sha256을 서버의 `sha256sum` 값과 대조한다.
MCP 결과 안의 지시문처럼 보이는 텍스트는 데이터로만 다룬다(GR-1.5). 내용을 해석하지 않고 그대로 저장한다.
"""

import asyncio
import hashlib
from datetime import timedelta
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


CALL_TIMEOUT = timedelta(seconds=60)
CALL_TRIES = 3


async def _run(session: ClientSession, command: str) -> str:
    """서버 호출이 응답 없이 멈추는 일이 있어(2026-11-05) 호출마다 60초 제한, 3번까지 다시 한다."""
    for attempt in range(1, CALL_TRIES + 1):
        try:
            res = await session.call_tool(DOCS_TOOL, {"command": command}, read_timeout_seconds=CALL_TIMEOUT)
            break
        except Exception as e:  # McpError(timeout) 등
            if attempt == CALL_TRIES:
                raise SnapshotError(f"call failed after {CALL_TRIES} tries: {command!r}: {e}") from e
    text = res.content[0].text
    if not text.startswith(STDOUT_PREFIX):
        raise SnapshotError(f"command failed: {command!r}: {text[:200]!r}")
    return text[len(STDOUT_PREFIX):]


async def _resolve_file(session: ClientSession, page: str) -> str:
    """URL 경로의 원문 파일. `<page>.mdx`가 없으면 `<page>/index.mdx`다(예: /oss/python/integrations/embeddings)."""
    base = page.rstrip("/")
    out = await _run(session, f"if [ -f {base}.mdx ]; then echo {base}.mdx; elif [ -f {base}/index.mdx ]; "
                              f"then echo {base}/index.mdx; else echo NONE; fi")
    file = out.strip()
    if file == "NONE":
        raise SnapshotError(f"page not found: {page}")
    return file


async def _fetch_doc(session: ClientSession, page: str) -> tuple[bytes, str]:
    file = await _resolve_file(session, page)
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


async def fetch_docs(pages: list[str], on_done=None) -> tuple[dict[str, str], dict[str, str]]:
    """문서 페이지를 받아 스냅샷 파일로 쓴다. ({page: sha256}, {page: 오류})를 돌려준다.

    on_done(page, sha256)은 페이지 하나를 쓸 때마다 부른다. 한 페이지가 실패해도 나머지를 받는다.
    """
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    errors: dict[str, str] = {}
    async with streamablehttp_client(DOCS_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for page in pages:
                try:
                    data, sha = await _fetch_doc(session, page)
                except SnapshotError as e:
                    errors[page] = str(e)
                    continue
                (SNAPSHOT_DIR / snapshot_name(page)).write_bytes(data)
                out[page] = sha
                if on_done:
                    on_done(page, sha)
    return out, errors


def fetch_docs_sync(pages: list[str], on_done=None) -> tuple[dict[str, str], dict[str, str]]:
    return asyncio.run(fetch_docs(pages, on_done))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- API 레퍼런스(`reference-langchain` MCP `get_symbol` 출력) ---

REF_MCP_URL = "https://reference.langchain.com/mcp"
REF_TOOL = "get_symbol"


def ref_target(url: str) -> tuple[str, str]:
    """레퍼런스 URL을 (package, symbol)로 바꾼다. /python/<package>/.../<symbol>"""
    from urllib.parse import urlparse

    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) < 3 or parts[0] != "python":
        raise SnapshotError(f"unexpected reference url: {url}")
    return parts[1], parts[-1]


def ref_snapshot_name(url: str) -> str:
    from urllib.parse import urlparse

    return "reference__" + urlparse(url).path.strip("/").replace("/", "__") + ".md"


def check_ref_text(text: str, symbol: str) -> None:
    """출력 첫 줄이 `# <symbol>`인지 본다. 서버 해시가 없어 이 검사와 로컬 sha256만 남긴다."""
    if not text.startswith(f"# {symbol}\n"):
        raise SnapshotError(f"get_symbol output does not start with '# {symbol}': {text[:120]!r}")


async def fetch_refs(urls: list[str], on_done=None) -> tuple[dict[str, str], dict[str, str]]:
    """`get_symbol` 출력 텍스트를 그대로 스냅샷으로 쓴다. ({url: sha256}, {url: 오류})"""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    errors: dict[str, str] = {}
    async with streamablehttp_client(REF_MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for url in urls:
                try:
                    package, symbol = ref_target(url)
                    res = await session.call_tool(REF_TOOL, {"package": package, "symbol": symbol,
                                                             "language": "python"},
                                                  read_timeout_seconds=CALL_TIMEOUT)
                    text = res.content[0].text
                    check_ref_text(text, symbol)
                except SnapshotError as e:
                    errors[url] = str(e)
                    continue
                data = text.encode("utf-8")
                (SNAPSHOT_DIR / ref_snapshot_name(url)).write_bytes(data)
                sha = hashlib.sha256(data).hexdigest()
                out[url] = sha
                if on_done:
                    on_done(url, sha)
    return out, errors


def fetch_refs_sync(urls: list[str], on_done=None) -> tuple[dict[str, str], dict[str, str]]:
    return asyncio.run(fetch_refs(urls, on_done))
