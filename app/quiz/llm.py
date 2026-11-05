"""Bedrock 모델 생성(design.md 8.1, 3.2, D-8, D-12). 생성 경로(CLI)에서만 쓴다.

Anthropic API를 직접 부르지 않는다(C-2). 서버와 샌드박스는 이 모듈을 쓰지 않는다.
"""

import os

from botocore.config import Config
from langchain_aws import ChatBedrockConverse

GEN_MODEL = "global.anthropic.claude-sonnet-4-6"
JUDGE_MODEL = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
ALLOWED_REGIONS = ("us-east-1", "us-west-2", "ap-northeast-2")

BOTO_CONFIG = Config(
    connect_timeout=10,
    read_timeout=120,
    retries={"mode": "adaptive", "max_attempts": 5},
)


class RegionError(RuntimeError):
    pass


def region() -> str:
    """`AWS_REGION`을 읽는다. 없으면 `AWS_DEFAULT_REGION`을 읽는다. 세 리전 밖이면 멈춘다."""
    value = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if value not in ALLOWED_REGIONS:
        raise RegionError(f"AWS_REGION must be one of {ALLOWED_REGIONS}, got {value!r}")
    return value


def chat_model(model_id: str, temperature: float | None = None) -> ChatBedrockConverse:
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    return ChatBedrockConverse(model=model_id, region_name=region(), config=BOTO_CONFIG, **kwargs)


def gen_model() -> ChatBedrockConverse:
    return chat_model(GEN_MODEL)


def judge_model() -> ChatBedrockConverse:
    return chat_model(JUDGE_MODEL, temperature=0)


def usage(message) -> tuple[int, int]:
    """AIMessage에서 (입력 토큰, 출력 토큰)을 꺼낸다."""
    meta = getattr(message, "usage_metadata", None) or {}
    return int(meta.get("input_tokens", 0)), int(meta.get("output_tokens", 0))
