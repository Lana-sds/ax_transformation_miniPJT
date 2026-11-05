"""생성 모델 프로필 전환(2026-11-05 사용자 결정). Bedrock을 부르지 않는다.

global 프로필이 일일 토큰 한도("per day" 스로틀)에 걸리면 US 프로필로 넘어가고, 그 뒤로는 넘어간 프로필을 쓴다.
"""

import pytest
from botocore.exceptions import ClientError

from llm_fakes import FakeModel
from quiz import llm, pricing
from quiz.pipeline import nodes
from test_generate import payload, state

DAILY = "Too many tokens per day, please wait before trying again."


def client_error(code: str, message: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "Converse")


class Raising(FakeModel):
    """invoke마다 정해진 예외를 낸다."""

    def __init__(self, model_id, exc):
        super().__init__(payload("single"))
        self.model_id = model_id
        self.exc = exc
        self.calls = 0

    def with_structured_output(self, schema, include_raw=False):
        parent = self

        class S:
            def invoke(self, prompt):
                parent.calls += 1
                raise parent.exc

        return S()


class Ok(FakeModel):
    def __init__(self, model_id):
        super().__init__(payload("single"))
        self.model_id = model_id


def test_daily_throttle_detection():
    assert llm.is_daily_throttle(client_error("ThrottlingException", DAILY))
    assert not llm.is_daily_throttle(client_error("ThrottlingException", "Too many requests, please wait."))
    assert not llm.is_daily_throttle(client_error("ValidationException", "per day"))
    assert not llm.is_daily_throttle(ValueError(DAILY))


def test_failover_on_daily_throttle_and_stays():
    primary = Raising("p", client_error("ThrottlingException", DAILY))
    fallback = Ok("f")
    model = llm.FailoverModel([primary, fallback])
    s = model.with_structured_output(nodes.SCHEMAS["single"], include_raw=True)
    out = s.invoke("x")
    assert out["parsed"] is not None
    assert out["model_id"] == "f"
    assert model.model_id == "f"
    s.invoke("y")
    assert primary.calls == 1  # 넘어간 뒤에는 primary를 다시 부르지 않는다
    assert len(fallback.prompts) == 2


def test_other_errors_do_not_fail_over():
    primary = Raising("p", client_error("ValidationException", "bad input"))
    fallback = Ok("f")
    s = llm.FailoverModel([primary, fallback]).with_structured_output(nodes.SCHEMAS["single"], include_raw=True)
    with pytest.raises(ClientError):
        s.invoke("x")
    assert fallback.prompts == []


def test_all_profiles_throttled_raises():
    a = Raising("a", client_error("ThrottlingException", DAILY))
    b = Raising("b", client_error("ThrottlingException", DAILY))
    s = llm.FailoverModel([a, b]).with_structured_output(nodes.SCHEMAS["single"], include_raw=True)
    with pytest.raises(ClientError):
        s.invoke("x")
    assert (a.calls, b.calls) == (1, 1)


def test_gen_model_is_failover_global_then_us(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    model = llm.gen_model()
    assert isinstance(model, llm.FailoverModel)
    assert [m.model_id for m in model.models] == [llm.GEN_MODEL, llm.GEN_FALLBACK_MODEL]
    assert llm.GEN_MODEL == "global.anthropic.claude-sonnet-4-6"
    assert llm.GEN_FALLBACK_MODEL == "us.anthropic.claude-sonnet-4-6"


def test_pricing_has_fallback_model():
    price = pricing.load()["models"][llm.GEN_FALLBACK_MODEL]
    assert (price["input"], price["output"]) == (3.3, 16.5)


def test_node_cost_uses_model_actually_called():
    primary = Raising(llm.GEN_MODEL, client_error("ThrottlingException", DAILY))
    fallback = Ok(llm.GEN_FALLBACK_MODEL)
    out = nodes.generate(state("single"), llm.FailoverModel([primary, fallback]))
    assert out["fail_reasons"] == []
    expected = pricing.cost(llm.GEN_FALLBACK_MODEL, 100, 20)
    assert abs(out["tokens"]["cost_usd"] - expected) < 1e-12
