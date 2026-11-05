"""프롬프트 로더. 기본 디렉토리는 `packs/langchain/prompts/`다.

환경 변수 `QUIZ_PROMPTS_DIR`이 있으면 그 디렉토리에서 읽는다(04 실험 arm). 호출할 때마다 읽으므로
테스트와 arm마다 바꿀 수 있다. 상대 경로는 현재 작업 디렉토리 기준이다(`QUIZ_DB`와 같다).
변형 디렉토리는 기본 디렉토리 전체 사본이어야 한다. 이름으로 파일을 찾으므로 빠진 파일은 실패한다.
"""

import os
from pathlib import Path

from quiz.db import REPO_ROOT

ENV = "QUIZ_PROMPTS_DIR"
DEFAULT_PROMPT_DIR = REPO_ROOT / "packs" / "langchain" / "prompts"
PROMPT_DIR = DEFAULT_PROMPT_DIR  # 하위 호환. 실제 경로는 prompt_dir()로 읽는다


def prompt_dir() -> Path:
    override = os.environ.get(ENV)
    return Path(override) if override else DEFAULT_PROMPT_DIR


def is_overridden() -> bool:
    """기본 디렉토리가 아닌 곳을 가리키면 True다."""
    return prompt_dir().resolve() != DEFAULT_PROMPT_DIR.resolve()


def load(name: str) -> str:
    return (prompt_dir() / f"{name}.md").read_text(encoding="utf-8")


def render(name: str, **values: str) -> str:
    text = load(name)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text
