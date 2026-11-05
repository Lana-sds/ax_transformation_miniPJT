"""`packs/langchain/prompts/` 프롬프트 로더."""

from quiz.db import REPO_ROOT

PROMPT_DIR = REPO_ROOT / "packs" / "langchain" / "prompts"


def load(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")


def render(name: str, **values: str) -> str:
    text = load(name)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text
