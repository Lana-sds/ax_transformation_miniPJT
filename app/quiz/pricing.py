"""Bedrock 단가표(`data/pricing/bedrock.yaml`)와 호출 비용 계산(US-7.2, T2.8).

단가가 없는 모델은 비용을 None으로 둔다. 배치 `cost_usd`는 시도 행 비용이 모두 있을 때만 채운다.
"""

from functools import lru_cache

import yaml

from quiz.db import REPO_ROOT

PRICING_PATH = REPO_ROOT / "data" / "pricing" / "bedrock.yaml"
PER = 1_000_000


@lru_cache(maxsize=1)
def load() -> dict:
    if not PRICING_PATH.exists():
        return {"models": {}}
    return yaml.safe_load(PRICING_PATH.read_text(encoding="utf-8")) or {"models": {}}


def cost(model_id: str | None, input_tokens: int, output_tokens: int, table: dict | None = None) -> float | None:
    price = ((table or load()).get("models") or {}).get(model_id) if model_id else None
    if not price:
        return None
    return (input_tokens * price["input"] + output_tokens * price["output"]) / PER
