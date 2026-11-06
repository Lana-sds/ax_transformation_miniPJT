"""코드형 보기 실행 클라이언트(design.md 8.2, T2.5).

앱은 샌드박스를 subprocess로만 부른다. stdin JSON 하나를 주고 stdout JSON 한 줄을 받는다.
자식 환경은 허용 목록(`ALLOW_KEYS`)에 있는 변수만 넘긴다. `AWS_*`, `LANGFUSE_*`, `QUIZ_DB`, 토큰,
`USERPROFILE`은 넘기지 않는다(F-1). 자식의 cwd는 실행마다 새로 만든 임시 디렉토리이고, 끝나면 지운다.
실행기(runner.py)는 그 디렉토리 밖 쓰기와 허용 범위 밖 읽기를 감사 훅으로 막는다.
보기 1개당 30초가 지나면 프로세스를 끝내고 `timeout`으로 둔다.
샌드박스 가상 환경은 `uv sync --project sandbox`로 만든다. `uv run`을 거치지 않고 그 Python을 바로 부른다.
그래야 타임아웃 때 끝낼 프로세스가 실행기 자신이다.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from quiz.db import REPO_ROOT

SANDBOX_DIR = REPO_ROOT / "sandbox"
TIMEOUT_SEC = 30
# Windows에서 Python과 numpy가 도는 데 필요한 것만 넘긴다. 이름은 대문자로 비교한다.
ALLOW_KEYS = ("SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "PATH", "PATHEXT", "COMSPEC",
              "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "OS")
# 허용 목록에 있어도 넘기지 않는다(이중 안전장치).
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


def child_env(env: dict[str, str] | None = None, workdir: str | Path | None = None) -> dict[str, str]:
    """자식 프로세스 환경. 허용 목록만 넘기고, 임시 디렉토리는 작업 디렉토리로 돌린다."""
    env = dict(os.environ if env is None else env)
    clean = {k.upper(): v for k, v in env.items()
             if k.upper() in ALLOW_KEYS and not k.upper().startswith(STRIP_PREFIXES) and k.upper() not in STRIP_KEYS}
    clean["PYTHONIOENCODING"] = "utf-8"
    clean["PYTHONDONTWRITEBYTECODE"] = "1"
    if workdir is not None:
        clean["TEMP"] = clean["TMP"] = clean["TMPDIR"] = str(workdir)
    return clean


def lock_hash() -> str:
    return hashlib.sha256((SANDBOX_DIR / "uv.lock").read_bytes()).hexdigest()


def run(code: str, timeout: float = TIMEOUT_SEC) -> dict:
    """보기 코드 하나를 실행해 `{ok, stdout, error_type}`을 돌려준다."""
    python = python_path()
    # 실행마다 빈 작업 디렉토리를 만든다. 실행기는 이 디렉토리 안에만 쓸 수 있다. 끝나면 지운다.
    with tempfile.TemporaryDirectory(prefix="quiz-sandbox-", ignore_cleanup_errors=True) as work:
        try:
            proc = subprocess.run(
                [str(python), str(SANDBOX_DIR / "runner.py")],
                input=json.dumps({"code": code}), capture_output=True, text=True, encoding="utf-8",
                timeout=timeout, env=child_env(workdir=work), cwd=work,
            )
        except subprocess.TimeoutExpired:
            return dict(TIMEOUT)
    lines = proc.stdout.strip().splitlines()
    try:
        out = json.loads(lines[-1])
        return {"ok": bool(out["ok"]), "stdout": out["stdout"], "error_type": out["error_type"]}
    except (IndexError, ValueError, KeyError, TypeError):
        return {"ok": False, "stdout": "", "error_type": "SandboxError"}


MODULE_MISSING = "ModuleNotFoundError"


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
    - 실행이 `ModuleNotFoundError`이고 문서 기준이 그 오류가 아니면 `sandbox_module_missing`이다.
      샌드박스에 없는 패키지를 쓴 코드다. 버리지 않고 재생성한다(2026-11-05 승인).
    """
    if predicted is not None and same(actual, predicted) and same(actual, expected):
        return None
    if actual.get("error_type") == MODULE_MISSING and expected.get("error_type") != MODULE_MISSING:
        return "sandbox_module_missing"
    if predicted is not None and same(predicted, expected) and not same(actual, expected):
        return "version_conflict"
    return "judge_exec_mismatch"
