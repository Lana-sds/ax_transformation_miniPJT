"""코드형 보기 실행 클라이언트(design.md 8.2, T2.5).

앱은 샌드박스를 subprocess로만 부른다. stdin JSON 하나를 주고 stdout JSON 한 줄을 받는다.
자식 환경에서 `AWS_*`, `LANGFUSE_*`를 지운다. 보기 1개당 30초가 지나면 프로세스를 끝내고 `timeout`으로 둔다.
샌드박스 가상 환경은 `uv sync --project sandbox`로 만든다. `uv run`을 거치지 않고 그 Python을 바로 부른다.
그래야 타임아웃 때 끝낼 프로세스가 실행기 자신이다.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from quiz.db import REPO_ROOT

SANDBOX_DIR = REPO_ROOT / "sandbox"
TIMEOUT_SEC = 30
STRIP_PREFIXES = ("AWS_", "LANGFUSE_")
STRIP_KEYS = ("VIRTUAL_ENV",)  # 앱 가상 환경을 샌드박스에 넘기지 않는다
TIMEOUT = {"ok": False, "stdout": "", "error_type": "timeout"}


class SandboxNotReady(RuntimeError):
    pass


def python_path() -> Path:
    sub = ("Scripts", "python.exe") if sys.platform == "win32" else ("bin", "python")
    path = SANDBOX_DIR.joinpath(".venv", *sub)
    if not path.exists():
        raise SandboxNotReady(f"{path} not found. Run `uv sync --project sandbox --frozen` at the repo root.")
    return path


def child_env(env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if env is None else env)
    clean = {k: v for k, v in env.items() if not k.startswith(STRIP_PREFIXES) and k not in STRIP_KEYS}
    clean["PYTHONIOENCODING"] = "utf-8"
    return clean


def lock_hash() -> str:
    return hashlib.sha256((SANDBOX_DIR / "uv.lock").read_bytes()).hexdigest()


def run(code: str, timeout: float = TIMEOUT_SEC) -> dict:
    """보기 코드 하나를 실행해 `{ok, stdout, error_type}`을 돌려준다."""
    try:
        proc = subprocess.run(
            [str(python_path()), str(SANDBOX_DIR / "runner.py")],
            input=json.dumps({"code": code}), capture_output=True, text=True, encoding="utf-8",
            timeout=timeout, env=child_env(), cwd=SANDBOX_DIR,
        )
    except subprocess.TimeoutExpired:
        return dict(TIMEOUT)
    lines = proc.stdout.strip().splitlines()
    try:
        out = json.loads(lines[-1])
        return {"ok": bool(out["ok"]), "stdout": out["stdout"], "error_type": out["error_type"]}
    except (IndexError, ValueError, KeyError, TypeError):
        return {"ok": False, "stdout": "", "error_type": "SandboxError"}


def same(a: dict, b: dict) -> bool:
    """두 실행 결과가 같은지. stdout 끝 공백은 무시한다."""
    return (bool(a.get("ok")) == bool(b.get("ok"))
            and (a.get("error_type") or None) == (b.get("error_type") or None)
            and (a.get("stdout") or "").rstrip() == (b.get("stdout") or "").rstrip())


def compare(actual: dict, expected: dict, predicted: dict | None) -> str | None:
    """보기 1개 판정. None이면 일치다.

    - 실행 = Judge 예측 = 문서 기준 기대값이면 일치다.
    - 실행만 문서 기준과 다르고 Judge 예측은 문서 기준과 같으면 `version_conflict`다(GR-7.5).
    - 그 밖의 차이(예측 없음 포함)는 `judge_exec_mismatch`다.
    """
    if predicted is not None and same(actual, predicted) and same(actual, expected):
        return None
    if predicted is not None and same(predicted, expected) and not same(actual, expected):
        return "version_conflict"
    return "judge_exec_mismatch"
