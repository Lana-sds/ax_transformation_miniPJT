"""토큰·비용(T2.8, US-2.5, US-7.2). 단가표는 data/pricing/bedrock.yaml이다."""

from langchain_core.messages import AIMessage

from llm_fakes import FakeModel
from quiz import batch, llm, pricing, store
from quiz.pipeline import nodes
from test_batch import models
from test_generate import payload, state


def test_pricing_file_has_both_models_with_source():
    table = pricing.load()
    assert table["source"].startswith("https://")
    assert table["checked"] == "2026-11-05"
    for model in (llm.GEN_MODEL, llm.JUDGE_MODEL):
        price = table["models"][model]
        assert price["input"] > 0 and price["output"] > 0


def test_cost_per_million_tokens():
    table = {"models": {"m": {"input": 3.0, "output": 15.0}}}
    assert pricing.cost("m", 1_000_000, 100_000, table) == 4.5


def test_cost_unknown_model_is_none():
    assert pricing.cost("nope", 10, 10, {"models": {}}) is None
    assert pricing.cost(None, 10, 10, {"models": {}}) is None


class PricedFake(FakeModel):
    model_id = llm.GEN_MODEL


def test_node_adds_cost_for_priced_model():
    out = nodes.generate(state("single"), PricedFake(payload("single")))
    # 입력 100, 출력 20 토큰. 3.0, 15.0 USD / 1M
    assert abs(out["tokens"]["cost_usd"] - (100 * 3.0 + 20 * 15.0) / 1_000_000) < 1e-12


def test_node_cost_none_for_unpriced_model():
    out = nodes.generate(state("single"), FakeModel(payload("single")))
    assert out["tokens"]["cost_usd"] is None


def test_batch_tokens_equal_attempt_sum_and_cost_set(tmp_db, monkeypatch):
    monkeypatch.setattr(batch, "backup", lambda *a, **k: None)
    m = models()
    m["gen_model"].model_id = llm.GEN_MODEL
    m["judge_model"].model_id = llm.JUDGE_MODEL
    batch_id = batch.run_batch(plan="pilot", **m)
    row = tmp_db.execute("SELECT input_tokens, output_tokens, cost_usd FROM batches WHERE batch_id = ?",
                         (batch_id,)).fetchone()
    sums = tmp_db.execute(
        "SELECT SUM(v.input_tokens), SUM(v.output_tokens), SUM(v.cost_usd) FROM verification_results v "
        "JOIN questions q ON q.question_id = v.question_id WHERE q.batch_id = ?", (batch_id,)).fetchone()
    assert row[0] == sums[0] > 0
    assert row[1] == sums[1] > 0
    assert row[2] is not None and abs(row[2] - sums[2]) < 1e-12


def test_batch_cost_null_when_any_attempt_unpriced(tmp_db, monkeypatch):
    monkeypatch.setattr(batch, "backup", lambda *a, **k: None)
    batch_id = batch.run_batch(plan="pool", count=1, **models())
    assert tmp_db.execute("SELECT cost_usd FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()[0] is None


def test_usage_reads_message_tokens():
    msg = AIMessage(content="", usage_metadata={"input_tokens": 7, "output_tokens": 3, "total_tokens": 10})
    assert llm.usage(msg) == (7, 3)


def test_upsert_verification_writes_cost(tmp_db):
    from conftest import make_question
    make_question(tmp_db, "b20261105-99-001")
    store.upsert_verification(tmp_db, "b20261105-99-001", 0,
                              {"tokens": {"input": 1, "output": 2, "cost_usd": 0.5}, "fail_reasons": []})
    assert tmp_db.execute("SELECT cost_usd FROM verification_results").fetchone()[0] == 0.5
