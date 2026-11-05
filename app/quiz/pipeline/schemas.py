"""생성·Judge 구조화 출력 스키마(design.md 6.1). 형식마다 생성 스키마가 하나다(T2.1)."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from quiz.gates import normalize_short_answer

# CCA-F 도메인 5개(docs/01-requirements/input/candidate_ccaf.md "도메인별 비중")와 해당 없음
CcaFTag = Literal[
    "agentic_architecture",      # 1. Agentic Architecture & Orchestration
    "tool_mcp",                  # 2. Tool Design & MCP Integration
    "claude_code",               # 3. Claude Code Configuration & Workflows
    "prompt_structured_output",  # 4. Prompt Engineering & Structured Output
    "context_reliability",       # 5. Context Management & Reliability
    "n/a",
]


class Choice(BaseModel):
    id: str = Field(description="Choice label: A, B, C, ...")
    text: str = Field(description="Choice text in English")


class CodeChoice(BaseModel):
    id: str = Field(description="Choice label: A, B, C or D")
    code: str = Field(description="The Python snippet shown to the learner for this choice")


class Segment(BaseModel):
    segment_id: str = Field(description="s1, s2, ... in order")
    en: str = Field(description="An English phrase copied from the question stem")
    ko: str = Field(description="Faithful Korean translation of exactly that phrase")


class GroundingRecord(BaseModel):
    page: str = Field(description="Allowlisted page path, exactly as given")
    quote: str = Field(description="Verbatim contiguous text copied from the document, at least 30 characters")
    answer_basis: str = Field(description="Korean: how this quote supports the answer key")


class ExecResult(BaseModel):
    ok: bool = Field(description="True if the program finishes without an uncaught exception")
    stdout: str = Field(description="Exact text the program prints, including the trailing newline of print()")
    error_type: str | None = Field(description="Class name of the uncaught exception, or null if ok")


class ExecCase(BaseModel):
    choice_id: str = Field(description="The choice this program belongs to")
    code: str = Field(description="Complete runnable Python program for this choice (imports included)")
    expected: ExecResult = Field(description="What the program does according to the document")


class _Common(BaseModel):
    stem_en: str = Field(description="The question in English")
    explanation_ko: str = Field(description="Korean explanation. Keep API and class names in original English")
    segments: list[Segment] = Field(description="English-Korean phrase mapping that covers the whole stem")
    grounding_records: list[GroundingRecord] = Field(description="At least one record")
    cca_f_tag: CcaFTag = Field(description="Closest CCA-F domain, or 'n/a'")


def _ids(choices) -> list[str]:
    return [c.id for c in choices]


def _check_keys(answer_key: list[str], choices) -> None:
    ids = _ids(choices)
    if len(set(ids)) != len(ids):
        raise ValueError("choice ids must be unique")
    if not set(answer_key) <= set(ids) or len(set(answer_key)) != len(answer_key):
        raise ValueError("answer_key must be distinct choice ids")


class SingleQuestion(_Common):
    choices: list[Choice] = Field(description="Exactly four choices A-D", min_length=4, max_length=4)
    answer_key: list[str] = Field(description="The single correct choice id, e.g. ['B']", min_length=1, max_length=1)

    @model_validator(mode="after")
    def _valid(self):
        _check_keys(self.answer_key, self.choices)
        return self


class MultiQuestion(_Common):
    choices: list[Choice] = Field(description="Exactly five choices A-E", min_length=5, max_length=5)
    answer_key: list[str] = Field(description="All correct choice ids, 2 or 3 of them, e.g. ['A', 'D']",
                                  min_length=2, max_length=3)
    select_count: int = Field(description="Number of choices the learner must select; equals len(answer_key)")

    @model_validator(mode="after")
    def _valid(self):
        _check_keys(self.answer_key, self.choices)
        if self.select_count != len(self.answer_key):
            raise ValueError("select_count must equal len(answer_key)")
        self.answer_key = sorted(self.answer_key)
        return self


class ShortQuestion(_Common):
    answer_key: list[str] = Field(description="The one canonical answer, e.g. ['add_node']", min_length=1, max_length=1)
    accepted_answers: list[str] = Field(description="1-5 accepted spellings, including the canonical answer")

    @model_validator(mode="after")
    def _valid(self):
        accepted = {normalize_short_answer(a) for a in self.accepted_answers}
        if normalize_short_answer(self.answer_key[0]) not in accepted:
            raise ValueError("answer_key must be one of accepted_answers")
        return self


class CodeQuestion(_Common):
    choices: list[CodeChoice] = Field(description="Exactly four code choices A-D", min_length=4, max_length=4)
    answer_key: list[str] = Field(description="The single correct choice id, e.g. ['C']", min_length=1, max_length=1)
    exec_spec: list[ExecCase] = Field(description="One runnable program per choice, same order as choices")

    @model_validator(mode="after")
    def _valid(self):
        _check_keys(self.answer_key, self.choices)
        if sorted(c.choice_id for c in self.exec_spec) != sorted(_ids(self.choices)):
            raise ValueError("exec_spec must have exactly one program per choice")
        return self


SCHEMAS: dict[str, type[_Common]] = {
    "single": SingleQuestion,
    "multi": MultiQuestion,
    "short": ShortQuestion,
    "code": CodeQuestion,
}


class ExecPrediction(BaseModel):
    choice_id: str = Field(description="The choice whose program you predict")
    ok: bool = Field(description="True if the program finishes without an uncaught exception")
    stdout: str = Field(description="Exact text the program prints, including the trailing newline of print()")
    error_type: str | None = Field(description="Class name of the uncaught exception, or null if ok")


class JudgeVerdict(BaseModel):
    answer_key_correct: bool = Field(description="The answer key is exactly the set of correct choices")
    quote_supports_answer: bool = Field(description="The quotes support the answer key")
    distractors_wrong: bool = Field(description="Every other choice is actually wrong per the document")
    mapping_faithful: bool = Field(description="Every segment ko neither omits nor adds meaning to en")
    distractors_plausible: bool = Field(
        description="Formats with choices: every wrong choice carries a plausible misconception. Format short: true")
    no_cue: bool = Field(
        description="Formats with choices: the wording gives no cue to the answer. Format short: true")
    verdict: Literal["pass", "fail"]
    reasons: list[str] = Field(description="Short English reasons for any failed item; empty if pass")
    missing_variants: list[str] = Field(
        default_factory=list,
        description="Format short only: correct spellings of the answer missing from accepted_answers; else empty")
    exec_predictions: list[ExecPrediction] = Field(
        default_factory=list,
        description="Format code only: one prediction per choice program in exec_spec; else empty")
