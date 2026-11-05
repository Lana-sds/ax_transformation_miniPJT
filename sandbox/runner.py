"""코드형 보기 실행기(design.md 8.2).

stdin: JSON 하나 `{"code": "<python source>"}`.
stdout: JSON 한 줄 `{"ok": bool, "stdout": str, "error_type": str | null}`.

- 실행 코드가 print한 내용은 모아서 `stdout`에 담는다. 이 프로세스의 stdout에는 결과 한 줄만 쓴다.
- 잡히지 않은 예외는 클래스 이름을 `error_type`에 담는다. 입력 JSON이 틀리면 `InvalidInput`이다.
- 네트워크 연결은 막는다. 막힌 호출은 `NetworkBlockedError`로 드러난다.
- 결과 줄을 쓰면 종료 코드는 0이다. 시간 제한과 환경 변수 정리는 앱 쪽 클라이언트가 한다.
"""

import io
import json
import os
import socket
import sys
import threading

SANDBOX_DIR = os.path.dirname(os.path.abspath(__file__))


class NetworkBlockedError(OSError):
    """샌드박스 안에서 네트워크 연결을 시도했다."""


def _blocked(*args, **kwargs):
    raise NetworkBlockedError("network access is disabled in the sandbox")


_INET_FAMILIES = {socket.AF_INET, socket.AF_INET6}


def block_network() -> None:
    """외부 연결을 막는다. asyncio 이벤트 루프가 쓰는 socketpair만 예외로 둔다.

    Windows Proactor 루프는 `socket.connect`를 거치지 않고 ConnectEx로 연결한다.
    그래서 IP 소켓 생성 자체도 막는다.
    """
    allow = threading.local()
    real_init = socket.socket.__init__
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_socketpair = socket.socketpair

    def init(self, family=-1, type=-1, proto=-1, fileno=None):
        if fileno is None and not getattr(allow, "on", False):
            fam = socket.AF_INET if family == -1 else family
            if fam in _INET_FAMILIES:
                _blocked()
        real_init(self, family, type, proto, fileno)

    def connect(self, address):
        if getattr(allow, "on", False):
            return real_connect(self, address)
        _blocked()

    def connect_ex(self, address):
        if getattr(allow, "on", False):
            return real_connect_ex(self, address)
        _blocked()

    def socketpair(*args, **kwargs):
        # Windows의 socketpair는 루프백 connect로 만든다. 이 호출 동안만 connect를 허용한다.
        allow.on = True
        try:
            return real_socketpair(*args, **kwargs)
        finally:
            allow.on = False

    socket.socket.__init__ = init
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.socketpair = socketpair
    socket.create_connection = _blocked
    socket.getaddrinfo = _blocked
    socket.gethostbyname = _blocked
    socket.gethostbyname_ex = _blocked


def parse_input(raw: bytes) -> str | None:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("code"), str):
        return None
    return payload["code"]


def execute(code: str) -> dict:
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    ok, error_type = True, None
    try:
        exec(compile(code, "<exec_spec>", "exec"), {"__name__": "__main__"})
    except SystemExit as exc:
        if exc.code not in (None, 0):
            ok, error_type = False, "SystemExit"
    except BaseException as exc:  # noqa: BLE001 - 실행 코드의 모든 예외를 결과로 돌린다
        ok, error_type = False, type(exc).__name__
    finally:
        sys.stdout = old_stdout
    return {"ok": ok, "stdout": captured.getvalue(), "error_type": error_type}


def main() -> int:
    # 결과 줄만 원래 stdout으로 낸다. fd 1은 devnull로 돌려 C 확장이나 os.write 출력이 섞이지 않게 한다.
    result_fd = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.close(devnull)
    result_out = os.fdopen(result_fd, "w", encoding="utf-8", newline="\n")

    if SANDBOX_DIR not in sys.path:
        sys.path.insert(0, SANDBOX_DIR)

    code = parse_input(sys.stdin.buffer.read())
    if code is None:
        result = {"ok": False, "stdout": "", "error_type": "InvalidInput"}
    else:
        block_network()
        result = execute(code)

    result_out.write(json.dumps(result) + "\n")
    result_out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
