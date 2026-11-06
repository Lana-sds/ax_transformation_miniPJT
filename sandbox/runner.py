"""코드형 보기 실행기(design.md 8.2).

stdin: JSON 하나 `{"code": "<python source>"}`.
stdout: JSON 한 줄 `{"ok": bool, "stdout": str, "error_type": str | null}`.

- 실행 코드가 print한 내용은 모아서 `stdout`에 담는다. 이 프로세스의 stdout에는 결과 한 줄만 쓴다.
- 잡히지 않은 예외는 클래스 이름을 `error_type`에 담는다. 입력 JSON이 틀리면 `InvalidInput`이다.
- 네트워크 연결은 막는다. 막힌 호출은 `NetworkBlockedError`로 드러난다.
- 실행 직전에 감사 훅(`sys.addaudithook`)을 건다(F-1, F-2). 시작 시점의 작업 디렉토리(cwd)가
  유일한 쓰기 허용 범위다. 앱 클라이언트는 실행마다 빈 임시 디렉토리를 cwd로 준다.
  읽기는 그 디렉토리, Python 설치/가상 환경, 이 sandbox 디렉토리만 허용한다.
  파일, 프로세스, ctypes, sqlite3 차단은 `PermissionError`로 드러난다.
- 결과 줄을 쓰면 종료 코드는 0이다. 시간 제한과 환경 변수 정리는 앱 쪽 클라이언트가 한다.
"""

import importlib
import io
import json
import os
import socket
import sys
import tempfile

SANDBOX_DIR = os.path.dirname(os.path.abspath(__file__))

# 감사 훅을 걸기 전에 미리 import한다. 둘 다 import 시점에 ctypes로 kernel32를 부른다
# (ctypes: GetLastError, click._winconsole: GetStdHandle). httpx -> langgraph_sdk -> langchain이 click을 끌어온다.
# 훅이 ctypes를 막으므로 훅 뒤에 처음 import하면 langchain import가 깨진다.
_PRELOAD = ("ctypes", "click")


class NetworkBlockedError(OSError):
    """샌드박스 안에서 네트워크 연결을 시도했다."""


# --- 감사 훅 ---------------------------------------------------------------
#
# 감사 훅은 한 번 걸면 떼어 낼 수 없다(CPython에 제거 API가 없다). 실행 코드가 훅을 끄지 못하게
# 훅이 쓰는 함수와 값은 설치 시점에 지역 변수로 잡아 두고, 실행 코드가 바꿀 수 있는 모듈 속성
# (os.path.realpath 같은)은 훅 안에서 부르지 않는다.

# 프로세스 생성과 네이티브 탈출구. 이름이 이 접두어로 시작하는 이벤트는 모두 막는다.
_DENY_PREFIXES = (
    "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "os.startfile",
    "os.kill", "os.symlink", "os.link", "os.listdrives", "os.listmounts", "os.listvolumes",
    "ctypes.", "sqlite3.", "_winapi.", "winreg.", "msvcrt.open_osfhandle", "mmap.", "webbrowser.",
    "pty.", "gc.get_objects", "gc.get_referrers", "gc.get_referents",
    "sys._current_frames", "sys.settrace", "sys.setprofile", "sys.monitoring.",
)

# 경로 인자를 받는 쓰기 이벤트: 이벤트 이름 -> 쓰기 경로 인자 위치. 작업 디렉토리 안만 허용한다.
_WRITE_PATH_ARGS = {
    "os.remove": (0,), "os.rmdir": (0,), "os.mkdir": (0,), "os.rename": (0, 1), "os.chmod": (0,),
    "os.chown": (0,), "os.utime": (0,), "os.truncate": (0,), "os.chflags": (0,), "os.lchflags": (0,),
    "os.setxattr": (0,), "os.removexattr": (0,), "os.chdir": (0,),
    "shutil.rmtree": (0,), "shutil.move": (0, 1), "shutil.copytree": (1,), "shutil.copyfile": (1,),
    "shutil.copymode": (1,), "shutil.copystat": (1,), "shutil.chown": (0,), "shutil.unpack_archive": (1,),
    "tempfile.mkstemp": (0,), "tempfile.mkdtemp": (0,),
}
# 경로 인자를 받는 읽기 이벤트. 읽기 허용 범위 안만 허용한다.
_READ_PATH_ARGS = {
    "os.listdir": (0,), "os.scandir": (0,), "os.add_dll_directory": (0,), "os.listxattr": (0,),
    "os.getxattr": (0,), "shutil.copytree": (0,), "shutil.copyfile": (0,), "shutil.copymode": (0,),
    "shutil.copystat": (0,), "shutil.unpack_archive": (0,),
}
# dir_fd 인자 위치. -1/None이 아니면 경로를 풀 수 없으므로 막는다.
_DIR_FD_ARGS = {"os.remove": (1,), "os.rmdir": (1,), "os.mkdir": (2,), "os.rename": (2, 3), "os.chmod": (2,),
                "os.utime": (3,), "shutil.rmtree": (1,)}

_WRITE_FLAGS = (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
                | getattr(os, "O_TEMPORARY", 0))


def _make_resolver():
    """경로 문자열을 링크까지 푼 절대 경로(소문자)로 바꾸는 함수를 만든다.

    Windows에서는 C 함수 `nt._getfullpathname`(상대 경로, `..` 정리)과 `nt._getfinalpathname`
    (심볼릭 링크와 정션 풀기)만 쓴다. 실행 코드가 ntpath 모듈 속성을 바꿔도 훅 판정은 바뀌지 않는다.
    없는 경로는 존재하는 가장 가까운 상위 경로를 풀고 나머지를 붙인다.
    """
    fsenc, fserr = sys.getfilesystemencoding(), sys.getfilesystemencodeerrors()
    try:
        import nt
    except ImportError:  # Windows 밖에서는 realpath로 대신한다(이 저장소는 Windows만 쓴다)
        realpath = os.path.realpath

        def resolve(path):
            if type(path) is bytes:
                path = path.decode(fsenc, fserr)
            return realpath(path)
        return resolve

    full, final = nt._getfullpathname, nt._getfinalpathname

    def strip(p):
        if p.startswith("\\\\?\\UNC\\"):
            return "\\\\" + p[8:]
        if p.startswith("\\\\?\\"):
            return p[4:]
        return p

    def resolve(path):
        if type(path) is bytes:
            path = path.decode(fsenc, fserr)
        head, tail = full(path), ""
        while True:
            try:
                head = strip(final(head))
                break
            except (OSError, ValueError):
                parent, sep, name = head.rpartition("\\")
                if not sep or not parent or parent.endswith(":"):
                    break
                head, tail = parent, name + ("\\" + tail if tail else "")
        if tail:
            head = head + tail if head.endswith("\\") else head + "\\" + tail
        return head.lower()
    return resolve


def _under(path, roots):
    for root in roots:
        if path == root or path.startswith(root + "\\") or path.startswith(root + "/"):
            return True
    return False


def install_audit_hook(work_dir: str) -> None:
    """감사 훅을 건다. 이후 실행되는 코드 전체(모든 스레드)에 적용되고 되돌릴 수 없다.

    - 네트워크: `socket.*` 이벤트를 모두 막는다(`_socket` 직접 호출 포함). 예외는 Windows asyncio
      이벤트 루프가 쓰는 `socket.socketpair`(루프백 연결) 내부 호출뿐이다.
    - 파일: 쓰기는 `work_dir` 안만, 읽기는 `work_dir`, Python 설치/가상 환경, sandbox 디렉토리만 허용한다.
    - 프로세스, ctypes, sqlite3, winreg 등은 모두 막는다.
    """
    resolve = _make_resolver()
    work = resolve(work_dir)
    write_roots = (work,)
    read_roots = tuple(sorted({work, resolve(SANDBOX_DIR), *(resolve(p) for p in (
        sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix) if p)}))
    devnull = full_devnull = os.devnull.lower()
    try:
        import nt
        full_devnull = nt._getfullpathname(os.devnull).lower()
    except ImportError:
        pass

    getframe = sys._getframe
    deny_prefixes = _DENY_PREFIXES
    write_args, read_args, dir_fd_args = dict(_WRITE_PATH_ARGS), dict(_READ_PATH_ARGS), dict(_DIR_FD_ARGS)
    write_flags = _WRITE_FLAGS
    net_error = NetworkBlockedError

    # Windows의 socket.socketpair는 루프백 리스너에 connect해서 만든다(asyncio 이벤트 루프가 쓴다).
    # 이 함수 안의 호출만 허용한다. 호출 프레임의 코드 객체를 설치 시점 원본과 비교하므로
    # 실행 코드가 socket 모듈을 바꿔치기해도 허용 범위가 넓어지지 않는다.
    pair_code = getattr(getattr(socket, "_fallback_socketpair", None), "__code__", None)
    socket_internal = (socket.socket.__init__.__code__, socket.socket.accept.__code__)
    loopback = ("127.0.0.1", "::1")

    def denied(event, detail=""):
        return PermissionError(f"sandbox blocked {event} {detail}".rstrip())

    def check_path(event, path, write):
        if type(path) is int:  # 이미 연 파일 디스크립터. 여는 시점에 검사했다
            return
        if type(path) is not str and type(path) is not bytes:
            raise denied(event)
        try:
            resolved = resolve(path)
        except (OSError, ValueError, TypeError):
            raise denied(event) from None
        if resolved in (devnull, full_devnull):
            return
        if not _under(resolved, write_roots if write else read_roots):
            raise denied(event, repr(path))

    def in_socketpair():
        if pair_code is None:
            return False
        frame = getframe(3)  # 0: in_socketpair, 1: network, 2: hook, 3: 이벤트를 낸 호출의 파이썬 프레임
        while frame is not None and frame.f_code in socket_internal:
            frame = frame.f_back
        return frame is not None and frame.f_code is pair_code

    def network(event, args):
        if event == "socket.__new__" and in_socketpair():
            return
        if event in ("socket.bind", "socket.connect") and in_socketpair():
            address = args[1]
            if type(address) is tuple and address and address[0] in loopback:
                return
        raise net_error(f"network access is disabled in the sandbox ({event})")

    def hook(event, args):
        if event == "open":
            path, mode, flags = args
            if type(flags) is int:
                write = bool(flags & write_flags)
            else:
                write = type(mode) is not str or any(c in mode for c in "wax+")
            check_path(event, path, write)
            return
        if event.startswith("socket."):
            network(event, args)
            return
        if event.startswith(deny_prefixes):
            raise denied(event)
        if event in write_args or event in read_args:
            for i in dir_fd_args.get(event, ()):
                if i < len(args) and args[i] not in (None, -1):
                    raise denied(event, "dir_fd")
            for i in write_args.get(event, ()):
                if i < len(args):
                    check_path(event, "." if args[i] is None else args[i], True)
            for i in read_args.get(event, ()):
                if i < len(args):
                    check_path(event, "." if args[i] is None else args[i], False)

    sys.addaudithook(hook)


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


def prepare(work_dir: str) -> None:
    """훅을 걸기 전 준비. 미리 import하고, 임시 파일과 바이트코드가 작업 디렉토리 밖에 쓰이지 않게 한다."""
    for name in _PRELOAD:
        try:
            importlib.import_module(name)
        except ImportError:
            pass
    sys.dont_write_bytecode = True
    tempfile.tempdir = work_dir


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
        work_dir = os.getcwd()
        prepare(work_dir)
        install_audit_hook(work_dir)
        result = execute(code)

    result_out.write(json.dumps(result) + "\n")
    result_out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
