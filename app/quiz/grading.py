"""채점(FR-3, design.md 6.4). 형식별 채점 함수를 등록한다(NFR-1.2).

풀이 시점에 모델을 부르지 않는다(FR-3.4).
형식은 DB `CHECK`로 고정하지 않는다(5.2). 새 형식은 `register`로 채점 함수를 더한다.
- single, code, multi: 정답 키와 정확히 일치. 복수 선택은 부분 점수가 없다(FR-3.1).
- short: 4.4 정규화 뒤 허용 답안과 비교한다(FR-3.2). 정규화는 gates.normalize_short_answer 하나만 쓴다.
"""

from collections.abc import Callable

from quiz.gates import normalize_short_answer

Grader = Callable[[list[str], dict], bool]
_GRADERS: dict[str, Grader] = {}


class UnknownFormatError(ValueError):
    pass


def register(fmt: str):
    def deco(fn: Grader) -> Grader:
        _GRADERS[fmt] = fn
        return fn
    return deco


def unregister(fmt: str) -> None:
    _GRADERS.pop(fmt, None)


def registered_formats() -> list[str]:
    return sorted(_GRADERS)


def normalize_answer(answer: str | list[str]) -> list[str]:
    """제출 답을 보기 ID 목록으로 바꾼다. 복수 선택은 정렬한다(design.md 5.2)."""
    items = [answer] if isinstance(answer, str) else list(answer)
    return sorted(str(a).strip() for a in items)


@register("single")
@register("multi")
@register("code")
def _exact_key(answer: list[str], question: dict) -> bool:
    return sorted(answer) == sorted(question["answer_key"])


@register("short")
def _short(answer: list[str], question: dict) -> bool:
    if len(answer) != 1:
        return False
    submitted = normalize_short_answer(answer[0])
    if not submitted:
        return False
    accepted = {normalize_short_answer(a) for a in question.get("accepted_answers") or []}
    return submitted in accepted


def grade(fmt: str, answer: list[str], question: dict) -> bool:
    if fmt not in _GRADERS:
        raise UnknownFormatError(f"no grader registered for format {fmt!r}")
    return _GRADERS[fmt](answer, question)
