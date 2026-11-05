"""Bedrock 모델 생성(design.md 8.1, 3.2, D-8, D-12). 생성 경로(CLI)에서만 쓴다.

Anthropic API를 직접 부르지 않는다(C-2). 서버와 샌드박스는 이 모듈을 쓰지 않는다.
"""

import os
import threading

from botocore.config import Config
from langchain_aws import ChatBedrockConverse

GEN_MODEL = "global.anthropic.claude-sonnet-4-6"
# global 프로필이 일일 토큰 한도에 걸리면 쓰는 US 교차 리전 프로필. 한도가 따로다(2026-11-05 관찰).
GEN_FALLBACK_MODEL = "us.anthropic.claude-sonnet-4-6"
JUDGE_MODEL = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
JUDGE_FALLBACK_MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
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


def chat_model(model_id: str, temperature: float | None = None, region_name: str | None = None) -> ChatBedrockConverse:
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    return ChatBedrockConverse(model=model_id, region_name=region_name or region(), config=BOTO_CONFIG, **kwargs)


def profile_regions(model_id: str) -> tuple[str, ...]:
    """추론 프로필을 부를 수 있는 리전(bedrock-model-list.md). `us.` 프로필은 ap-northeast-2에 없다."""
    if model_id.startswith("us."):
        return ("us-east-1", "us-west-2")
    return ALLOWED_REGIONS


def region_order() -> tuple[str, ...]:
    """환경 변수 리전을 먼저, 나머지 허용 리전을 그 뒤에 둔다. 일일 한도는 소스 리전마다 따로다."""
    first = region()
    return (first,) + tuple(r for r in ALLOWED_REGIONS if r != first)


def is_daily_throttle(exc: BaseException) -> bool:
    """Bedrock 일일 토큰 한도 스로틀인지 본다. 분당 요청 스로틀은 아니다(그건 botocore가 재시도한다)."""
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    error = response.get("Error") or {}
    return error.get("Code") == "ThrottlingException" and "per day" in (error.get("Message") or "").lower()


class FailoverModel:
    """같은 모델의 추론 프로필 여러 개를 차례로 쓴다(2026-11-05 사용자 결정).

    지금 프로필이 일일 토큰 한도에 걸리면 다음 프로필로 넘어가고 그대로 머문다. 호출 하나에서
    프로필마다 한 번씩만 시도한다. 다른 오류는 그대로 낸다. 구조화 출력 결과에 실제로 부른 모델 ID를
    `model_id` 키로 붙인다. 단가를 그 모델로 매긴다.
    """

    def __init__(self, models: list):
        self.models = list(models)
        self._active = 0
        self._lock = threading.Lock()

    @property
    def model_id(self) -> str | None:
        return getattr(self.models[self._active], "model_id", None)

    def _call(self, invoke_on):
        with self._lock:
            start = self._active
        last = None
        for step in range(len(self.models)):
            idx = (start + step) % len(self.models)
            model = self.models[idx]
            try:
                out = invoke_on(model)
            except Exception as exc:  # noqa: BLE001 - 일일 한도만 넘기고 나머지는 다시 낸다
                if not is_daily_throttle(exc):
                    raise
                last = exc
                with self._lock:
                    if self._active == idx:
                        self._active = (idx + 1) % len(self.models)
                continue
            with self._lock:
                self._active = idx
            return out, getattr(model, "model_id", None)
        raise last

    def with_structured_output(self, schema, include_raw: bool = False):
        parent = self

        class _Structured:
            def invoke(self, prompt):
                out, model_id = parent._call(
                    lambda m: m.with_structured_output(schema, include_raw=include_raw).invoke(prompt))
                if include_raw:
                    out = {**out, "model_id": model_id}
                return out

        return _Structured()


def failover_chain(model_ids: tuple[str, ...], temperature: float | None = None) -> FailoverModel:
    """리전 순서대로, 리전 안에서는 프로필 순서대로 이어 붙인다."""
    return FailoverModel([chat_model(mid, temperature, region_name=r)
                          for r in region_order() for mid in model_ids if r in profile_regions(mid)])


# 배치 전체가 같은 인스턴스를 써야 전환한 프로필에 머문다.
_shared: dict[str, FailoverModel] = {}
_shared_lock = threading.Lock()


def reset_models() -> None:
    with _shared_lock:
        _shared.clear()


def _get(key: str, build) -> FailoverModel:
    with _shared_lock:
        if key not in _shared:
            _shared[key] = build()
        return _shared[key]


def gen_model() -> FailoverModel:
    return _get("gen", lambda: failover_chain((GEN_MODEL, GEN_FALLBACK_MODEL)))


def judge_model() -> FailoverModel:
    return _get("judge", lambda: failover_chain((JUDGE_MODEL, JUDGE_FALLBACK_MODEL), temperature=0))


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
