"""샌드박스 클라이언트와 execute 노드(T2.5, design.md 6.1·8.2). 실제 sandbox/ 실행기를 subprocess로 부른다."""

import hashlib

import pytest

from quiz import sandbox_client
from quiz.pipeline import nodes

OK_2 = {"ok": True, "stdout": "2\n", "error_type": None}


# --- 클라이언트 ---

def test_run_returns_runner_result():
    assert sandbox_client.run("print(1 + 1)") == OK_2


def test_run_reports_exception_class():
    out = sandbox_client.run("raise KeyError('x')")
    assert out["ok"] is False
    assert out["error_type"] == "KeyError"


def test_run_can_import_sandbox_fakes():
    code = "from fakes import GenericFakeChatModel\nprint(GenericFakeChatModel(messages=iter(['hi'])).invoke('x').content)"
    assert sandbox_client.run(code) == {"ok": True, "stdout": "hi\n", "error_type": None}


def test_infinite_loop_times_out():
    out = sandbox_client.run("while True:\n    pass", timeout=2)
    assert out == {"ok": False, "stdout": "", "error_type": "timeout"}


def test_default_timeout_is_30_seconds():
    assert sandbox_client.TIMEOUT_SEC == 30


def test_aws_and_langfuse_env_not_passed(monkeypatch):
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "secret")
    monkeypatch.setenv("QUIZ_KEEP_ME", "kept")
    code = ("import os\n"
            "print(sorted(k for k in os.environ if k.startswith(('AWS_', 'LANGFUSE_'))))\n"
            "print(os.environ.get('QUIZ_KEEP_ME'))")
    assert sandbox_client.run(code)["stdout"] == "[]\nkept\n"


def test_child_env_strips_prefixes_and_virtualenv():
    env = sandbox_client.child_env({"AWS_X": "1", "LANGFUSE_Y": "2", "VIRTUAL_ENV": "/app/.venv", "PATH": "p"})
    assert "AWS_X" not in env and "LANGFUSE_Y" not in env and "VIRTUAL_ENV" not in env
    assert env["PATH"] == "p"


def test_lock_hash_is_sha256_of_sandbox_lock():
    expected = hashlib.sha256((sandbox_client.SANDBOX_DIR / "uv.lock").read_bytes()).hexdigest()
    assert sandbox_client.lock_hash() == expected


# --- 판정 ---

def test_compare_all_equal_is_match():
    assert sandbox_client.compare(OK_2, OK_2, OK_2) is None


def test_compare_ignores_trailing_whitespace_in_stdout():
    assert sandbox_client.compare(OK_2, {**OK_2, "stdout": "2"}, OK_2) is None


def test_compare_version_conflict_when_judge_agrees_with_document():
    actual = {"ok": False, "stdout": "", "error_type": "TypeError"}
    assert sandbox_client.compare(actual, OK_2, OK_2) == "version_conflict"


def test_compare_judge_exec_mismatch_when_judge_disagrees_with_run():
    predicted = {"ok": False, "stdout": "", "error_type": "ValueError"}
    assert sandbox_client.compare(OK_2, OK_2, predicted) == "judge_exec_mismatch"


def test_compare_missing_prediction_is_mismatch():
    assert sandbox_client.compare(OK_2, OK_2, None) == "judge_exec_mismatch"


def test_compare_timeout_not_predicted_is_mismatch():
    timeout = {"ok": False, "stdout": "", "error_type": "timeout"}
    assert sandbox_client.compare(timeout, OK_2, {**OK_2, "stdout": "3\n"}) == "judge_exec_mismatch"


# --- execute 노드 ---

def code_state(predictions, expected=OK_2):
    spec = [{"choice_id": c, "code": f"print({c!r})", "expected": expected} for c in "AB"]
    return {
        "slot": {"format": "code"},
        "question": {"format": "code", "exec_spec": spec},
        "judge": {"exec_predictions": predictions},
        "fail_reasons": [],
    }


def fake_run(results):
    return lambda code: results[code]


def test_execute_skips_non_code():
    assert nodes.execute({"slot": {"format": "single"}, "question": {"format": "single"}, "fail_reasons": []}) == {}


def test_execute_match_sets_lock_hash_and_results():
    preds = [{"choice_id": c, **OK_2} for c in "AB"]
    out = nodes.execute(code_state(preds), fake_run({"print('A')": OK_2, "print('B')": OK_2}))
    assert out["exec_match"] == 1
    assert out["fail_reasons"] == []
    assert [r["choice_id"] for r in out["exec_result"]] == ["A", "B"]
    assert out["question"]["lock_hash"] == sandbox_client.lock_hash()


def test_execute_version_conflict():
    preds = [{"choice_id": c, **OK_2} for c in "AB"]
    broken = {"ok": False, "stdout": "", "error_type": "ImportError"}
    out = nodes.execute(code_state(preds), fake_run({"print('A')": OK_2, "print('B')": broken}))
    assert out["exec_match"] == 0
    assert out["fail_reasons"] == ["version_conflict"]


def test_execute_judge_exec_mismatch():
    preds = [{"choice_id": "A", **OK_2}, {"choice_id": "B", "ok": False, "stdout": "", "error_type": "KeyError"}]
    out = nodes.execute(code_state(preds), fake_run({"print('A')": OK_2, "print('B')": OK_2}))
    assert out["exec_match"] == 0
    assert out["fail_reasons"] == ["judge_exec_mismatch"]


def test_execute_with_real_sandbox():
    preds = [{"choice_id": "A", "ok": True, "stdout": "A\n", "error_type": None},
             {"choice_id": "B", "ok": True, "stdout": "B\n", "error_type": None}]
    st = code_state(preds)
    st["question"]["exec_spec"] = [
        {"choice_id": c, "code": f"print({c!r})", "expected": {"ok": True, "stdout": f"{c}\n", "error_type": None}}
        for c in "AB"]
    out = nodes.execute(st)
    assert out["exec_match"] == 1, out


@pytest.mark.parametrize("prior", [["judge_fail:answer_key_correct"]])
def test_execute_keeps_prior_fail_reasons(prior):
    preds = [{"choice_id": c, **OK_2} for c in "AB"]
    st = code_state(preds) | {"fail_reasons": prior}
    out = nodes.execute(st, fake_run({"print('A')": OK_2, "print('B')": OK_2}))
    assert out["fail_reasons"] == prior


# --- 샌드박스에 없는 모듈(2026-11-05 승인): 버전 충돌이 아니라 재생성 피드백 ---

MISSING = {"ok": False, "stdout": "", "error_type": "ModuleNotFoundError"}


def test_compare_module_not_found_is_sandbox_missing_not_version_conflict():
    assert sandbox_client.compare(MISSING, OK_2, OK_2) == "sandbox_module_missing"
    assert sandbox_client.compare(MISSING, OK_2, None) == "sandbox_module_missing"


def test_compare_module_not_found_expected_by_document_still_matches():
    assert sandbox_client.compare(MISSING, MISSING, MISSING) is None


def test_execute_module_missing_goes_to_regen():
    preds = [{"choice_id": c, **OK_2} for c in "AB"]
    out = nodes.execute(code_state(preds), fake_run({"print('A')": OK_2, "print('B')": MISSING}))
    assert out["fail_reasons"] == ["sandbox_module_missing"]
    assert nodes.decide({"fail_reasons": out["fail_reasons"], "regen_count": 0}) == ("regen", None)


def test_feedback_explains_sandbox_packages():
    out = nodes.feedback({"fail_reasons": ["sandbox_module_missing"], "judge": None, "regen_count": 0})
    assert out["feedback"][0] == "sandbox_module_missing"
    hint = " ".join(out["feedback"])
    for pkg in ("langchain", "langgraph", "langchain-core", "langchain-text-splitters", "numpy"):
        assert pkg in hint
