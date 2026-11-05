"""Langfuse 선택 적용(T2.9, design.md 8.3, NFR-5.4). 실제 Langfuse로 보내지 않는다."""

import pytest

from quiz import batch, llm
from quiz.pipeline import graph as slot_graph
from test_batch import models

KEYS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "LANGFUSE_BASE_URL")


@pytest.fixture
def no_langfuse(monkeypatch):
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)


@pytest.fixture
def fake_handler(monkeypatch):
    made = []
    monkeypatch.setattr(llm, "_langfuse_handler", lambda: made.append(object()) or made[-1])
    return made


def set_env(monkeypatch, host_key="LANGFUSE_HOST"):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv(host_key, "https://cloud.langfuse.com")


def test_disabled_without_env(no_langfuse):
    assert llm.langfuse_enabled() is False
    assert llm.trace_config("b20261105-01") == {}


@pytest.mark.parametrize("missing", ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"])
def test_disabled_unless_all_three(no_langfuse, monkeypatch, missing):
    set_env(monkeypatch)
    monkeypatch.delenv(missing)
    assert llm.langfuse_enabled() is False


@pytest.mark.parametrize("host_key", ["LANGFUSE_HOST", "LANGFUSE_BASE_URL"])
def test_enabled_with_either_host_key(no_langfuse, monkeypatch, host_key):
    set_env(monkeypatch, host_key)
    assert llm.langfuse_enabled() is True


def test_trace_config_has_batch_id_as_session_and_tag(no_langfuse, monkeypatch, fake_handler):
    set_env(monkeypatch)
    cfg = llm.trace_config("b20261105-01")
    assert cfg["callbacks"] == fake_handler
    assert cfg["metadata"]["langfuse_session_id"] == "b20261105-01"
    assert "b20261105-01" in cfg["metadata"]["langfuse_tags"]


def test_batch_runs_without_langfuse(no_langfuse, tmp_db, monkeypatch):
    monkeypatch.setattr(batch, "backup", lambda *a, **k: None)
    batch_id = batch.run_batch(plan="pool", count=1, **models())
    assert batch.unfinished(batch_id) == 0


def test_batch_passes_trace_config_to_graph(no_langfuse, tmp_db, monkeypatch, fake_handler):
    monkeypatch.setattr(batch, "backup", lambda *a, **k: None)
    monkeypatch.setattr(llm, "flush_traces", lambda: None)
    set_env(monkeypatch)
    seen = []
    real = slot_graph.run

    def spy(graph, state, config=None):
        seen.append(config)
        return real(graph, state)
    monkeypatch.setattr(slot_graph, "run", spy)
    batch_id = batch.run_batch(plan="pool", count=1, **models())
    assert seen and seen[0]["metadata"]["langfuse_session_id"] == batch_id
