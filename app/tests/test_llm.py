import pytest

from quiz import llm


def test_region_rejects_outside_allowed(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    with pytest.raises(llm.RegionError):
        llm.region()


def test_region_falls_back_to_default_region(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    assert llm.region() == "us-east-1"
