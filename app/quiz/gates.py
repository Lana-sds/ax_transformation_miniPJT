"""결정적 검사(design.md 4.4, US-2.1). 표준 라이브러리만 쓴다. 모델 호출과 DB 쓰기를 하지 않는다."""

import re
import unicodedata

MIN_QUOTE_CHARS = 30
_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """NFKC 정규화와 연속 공백(줄바꿈 포함) 1칸 축약만 한다. 대소문자와 마크다운 기호는 그대로 둔다(D-2)."""
    return _WS.sub(" ", unicodedata.normalize("NFKC", text)).strip()


def check_quote(quote: str, snapshot: str) -> str | None:
    q = normalize(quote)
    if len(q) < MIN_QUOTE_CHARS:
        return "quote_too_short"
    if q not in normalize(snapshot):
        return "quote_mismatch"
    return None


def check_page(page: str, allowed_pages: set[str]) -> str | None:
    return None if page in allowed_pages else "page_not_allowed"


def check_segments(segments: list[dict]) -> str | None:
    if not segments:
        return "mapping_missing"
    for seg in segments:
        if not (seg.get("segment_id") and seg.get("en") and seg.get("ko")):
            return "mapping_missing"
    return None


def run_gates(question: dict, snapshots: dict[str, str], allowed_pages: set[str]) -> list[str]:
    """실패 이유 목록을 돌려준다. 빈 목록이면 통과다.

    snapshots: {page: 스냅샷 원문}
    """
    fails: list[str] = []
    if (f := check_segments(question.get("segments", []))):
        fails.append(f)
    records = question.get("grounding_records", [])
    if not records:
        fails.append("grounding_missing")
    for rec in records:
        if (f := check_page(rec["page"], allowed_pages)):
            fails.append(f)
            continue
        if (f := check_quote(rec["quote"], snapshots[rec["page"]])):
            fails.append(f)
    return fails
