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


# --- Langfuse(design.md 8.3, NFR-5.4) ---
# SDK 5.1.0은 호스트를 `LANGFUSE_BASE_URL`로 읽고, 없으면 deprecated 키 `LANGFUSE_HOST`를 읽는다.
LANGFUSE_KEYS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
LANGFUSE_HOST_KEYS = ("LANGFUSE_BASE_URL", "LANGFUSE_HOST")


def langfuse_enabled() -> bool:
    """키 2개와 호스트 키가 모두 있을 때만 켠다."""
    return all(os.environ.get(k) for k in LANGFUSE_KEYS) and any(os.environ.get(k) for k in LANGFUSE_HOST_KEYS)


def _langfuse_handler():
    from langfuse.langchain import CallbackHandler

    return CallbackHandler()


def trace_config(batch_id: str) -> dict:
    """그래프 실행 config. Langfuse가 꺼져 있으면 빈 dict다. `batch_id`를 세션 ID와 태그로 단다."""
    if not langfuse_enabled():
        return {}
    return {
        "callbacks": [_langfuse_handler()],
        "metadata": {"langfuse_session_id": batch_id, "langfuse_tags": [batch_id]},
    }


def flush_traces() -> None:
    if langfuse_enabled():
        from langfuse import get_client

        get_client().flush()
