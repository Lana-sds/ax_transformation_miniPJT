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


SOURCE_TAIL_CHARS = 120


def source_near_quote(quote: str, snapshot: str) -> str | None:
    """인용 앞부분과 맞는 스냅샷 원문 구간을 돌려준다(재생성 피드백용, design.md 6.1).

    정규화한 인용의 가장 긴 앞부분(최소 MIN_QUOTE_CHARS자)이 정규화한 스냅샷에 있으면, 그 자리부터
    인용 길이 + SOURCE_TAIL_CHARS자를 돌려준다. 앞부분이 없으면 None이다. 판정에는 쓰지 않는다.
    """
    q, s = normalize(quote), normalize(snapshot)
    if len(q) < MIN_QUOTE_CHARS or q[:MIN_QUOTE_CHARS] not in s:
        return None
    lo, hi = MIN_QUOTE_CHARS, len(q)  # 앞부분이 있는지는 길이에 대해 단조라 이분 탐색한다
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if q[:mid] in s:
            lo = mid
        else:
            hi = mid - 1
    start = s.index(q[:lo])
    return s[start:start + len(q) + SOURCE_TAIL_CHARS]


def check_page(page: str, allowed_pages: set[str]) -> str | None:
    return None if page in allowed_pages else "page_not_allowed"


def check_segments(segments: list[dict]) -> str | None:
    if not segments:
        return "mapping_missing"
    for seg in segments:
        if not (seg.get("segment_id") and seg.get("en") and seg.get("ko")):
            return "mapping_missing"
    return None


MIN_ACCEPTED_ANSWERS = 1
MAX_ACCEPTED_ANSWERS = 5
SHORT_FORMAT = "short"


def check_accepted_answers(accepted: list[str] | None) -> str | None:
    """단답 허용 답안은 1~5개다(4.4, D-3). 없으면 0개로 본다."""
    n = len(accepted or [])
    if MIN_ACCEPTED_ANSWERS <= n <= MAX_ACCEPTED_ANSWERS:
        return None
    return "accepted_answers_count"


_TRAILING_CALL = re.compile(r"\(\)$")


def normalize_short_answer(text: str) -> str:
    """단답 채점 정규화(4.4). 채점(grading.py)도 이 함수를 쓴다.

    NFKC, 대소문자 무시(casefold), 백틱 제거, 모든 공백 제거, 끝의 `()` 한 번 제거 순이다.
    공백을 먼저 지우므로 `add_node ( )`도 `add_node`가 된다.
    """
    s = unicodedata.normalize("NFKC", text).casefold().replace("`", "")
    s = _WS.sub("", s)
    return _TRAILING_CALL.sub("", s)


DUPLICATE_JACCARD = (6, 10)  # 0.6을 정수 비로 둔다. 경계값 비교에서 부동소수 오차를 피한다
_TOKEN = re.compile(r"\w+")


def stem_tokens(stem: str) -> set[str]:
    """문제 본문 토큰 집합. NFKC, casefold 뒤 단어 문자(`\\w+`)만 토큰으로 본다. 구두점과 백틱은 버린다."""
    return set(_TOKEN.findall(unicodedata.normalize("NFKC", stem).casefold()))


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _jaccard_at_least(a: set[str], b: set[str], ratio: tuple[int, int]) -> bool:
    union = len(a | b)
    if not union:
        return False
    num, den = ratio
    return len(a & b) * den >= num * union


def _quotes(question: dict) -> set[str]:
    return {normalize(r["quote"]) for r in question.get("grounding_records", []) if r.get("quote")}


def find_duplicate(question: dict, others: list[dict]) -> str | None:
    """유사 중복 대상의 `question_id`를 돌려준다. 없으면 None이다(4.4, D-4).

    others: 같은 버킷의 `passed` 문제. 버킷 거르기는 호출하는 쪽이 한다.
    (1) 정규화한 quote가 하나라도 같거나 (2) 본문 토큰 Jaccard ≥ 0.6이면 중복이다.
    같은 `question_id`(재개 때 자기 자신)는 건너뛴다.
    """
    qid = question.get("question_id")
    quotes = _quotes(question)
    tokens = stem_tokens(question.get("stem_en", ""))
    for other in others:
        oid = other.get("question_id")
        if qid is not None and oid == qid:
            continue
        if quotes & _quotes(other):
            return oid
        if _jaccard_at_least(tokens, stem_tokens(other.get("stem_en", "")), DUPLICATE_JACCARD):
            return oid
    return None


def check_duplicate(question: dict, others: list[dict]) -> tuple[str | None, str | None]:
    """(실패 이유, duplicate_of). 중복이 아니면 (None, None)이다."""
    dup = find_duplicate(question, others)
    return ("duplicate", dup) if dup is not None else (None, None)


def run_gates(
    question: dict, snapshots: dict[str, str], allowed_pages: set[str], fmt: str | None = None
) -> list[str]:
    """실패 이유 목록을 돌려준다. 빈 목록이면 통과다.

    snapshots: {page: 스냅샷 원문}
    fmt: 문제 형식. 없으면 question["format"]을 쓴다. 단답이면 허용 답안 개수를 본다.
    유사 중복은 다른 문제가 필요하므로 여기서 보지 않는다(dedupe 노드가 check_duplicate를 부른다).
    """
    fails: list[str] = []
    if (f := check_segments(question.get("segments", []))):
        fails.append(f)
    if (fmt or question.get("format")) == SHORT_FORMAT:
        if (f := check_accepted_answers(question.get("accepted_answers"))):
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
