"""생성·Judge 구조화 출력 스키마(design.md 6.1). M0는 단일 선택만 다룬다."""

from typing import Literal

from pydantic import BaseModel, Field


class Choice(BaseModel):
    id: str = Field(description="Choice label: A, B, C or D")
    text: str = Field(description="Choice text in English")


class Segment(BaseModel):
    segment_id: str = Field(description="s1, s2, ... in order")
    en: str = Field(description="An English phrase copied from the question stem")
    ko: str = Field(description="Faithful Korean translation of exactly that phrase")


class GroundingRecord(BaseModel):
    page: str = Field(description="Allowlisted page path, exactly as given")
    quote: str = Field(description="Verbatim contiguous text copied from the document, at least 30 characters")
    answer_basis: str = Field(description="Korean: how this quote supports the answer key")


class GeneratedQuestion(BaseModel):
    stem_en: str = Field(description="The question in English")
    choices: list[Choice] = Field(description="Exactly four choices A-D")
    answer_key: list[str] = Field(description="The single correct choice id, e.g. ['B']")
    explanation_ko: str = Field(description="Korean explanation. Keep API and class names in original English")
    segments: list[Segment] = Field(description="English-Korean phrase mapping that covers the whole stem")
    grounding_records: list[GroundingRecord] = Field(description="At least one record")
    cca_f_tag: str = Field(description="CCA-F domain tag, or 'n/a'")


class JudgeVerdict(BaseModel):
    answer_key_correct: bool = Field(description="The answer key is the only correct choice")
    quote_supports_answer: bool = Field(description="The quotes support the answer key")
    distractors_wrong: bool = Field(description="Every other choice is actually wrong per the document")
    mapping_faithful: bool = Field(description="Every segment ko neither omits nor adds meaning to en")
    verdict: Literal["pass", "fail"]
    reasons: list[str] = Field(description="Short English reasons for any failed item; empty if pass")
