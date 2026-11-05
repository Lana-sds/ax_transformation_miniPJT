"""채점(FR-3, design.md 6.4). 형식별 채점 함수를 등록한다(NFR-1.2).

풀이 시점에 모델을 부르지 않는다(FR-3.4).
M0: 단일 선택, 코드 선택(정답 키와 정확히 일치). 복수 선택과 단답은 T1.2에서 더한다.
"""

from collections.abc import Callable

Grader = Callable[[list[str], dict], bool]
_GRADERS: dict[str, Grader] = {}


class UnknownFormatError(ValueError):
    pass


def register(fmt: str):
    def deco(fn: Grader) -> Grader:
        _GRADERS[fmt] = fn
        return fn
    return deco


def normalize_answer(answer: str | list[str]) -> list[str]:
    """제출 답을 보기 ID 목록으로 바꾼다. 복수 선택은 정렬한다(design.md 5.2)."""
    items = [answer] if isinstance(answer, str) else list(answer)
    return sorted(str(a).strip() for a in items)


@register("single")
@register("code")
def _exact_key(answer: list[str], question: dict) -> bool:
    return answer == sorted(question["answer_key"])


def grade(fmt: str, answer: list[str], question: dict) -> bool:
    if fmt not in _GRADERS:
        raise UnknownFormatError(f"no grader registered for format {fmt!r}")
    return _GRADERS[fmt](answer, question)
