"""runner.py를 subprocess로 실행해 stdin JSON -> stdout JSON 한 줄 계약을 확인한다."""

import json
import socket
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[1]
RUNNER = SANDBOX / "runner.py"


def run_raw(stdin: bytes, cwd: Path | None = None) -> subprocess.CompletedProcess:
    # 실행기의 작업 디렉토리(cwd)가 쓰기 허용 범위다. 앱 클라이언트처럼 매번 빈 임시 디렉토리를 준다.
    if cwd is None:
        with tempfile.TemporaryDirectory() as work:
            return run_raw(stdin, Path(work))
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        input=stdin,
        capture_output=True,
        cwd=cwd,
        timeout=120,
    )


def run_code(code: str, cwd: Path | None = None) -> dict:
    payload = json.dumps({"code": textwrap.dedent(code)}).encode("utf-8")
    proc = run_raw(payload, cwd=cwd)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    lines = proc.stdout.decode("utf-8").splitlines()
    assert len(lines) == 1, proc.stdout
    result = json.loads(lines[0])
    assert set(result) == {"ok", "stdout", "error_type"}
    return result


def test_print_is_captured():
    assert run_code("print(1+1)") == {"ok": True, "stdout": "2\n", "error_type": None}


def test_non_ascii_stdout_round_trips():
    result = run_code("print('해설 ok')")
    assert result["stdout"] == "해설 ok\n"


def test_uncaught_exception_reports_class_name():
    result = run_code(
        """
        print("before")
        raise ValueError("boom")
        """
    )
    assert result == {"ok": False, "stdout": "before\n", "error_type": "ValueError"}


def test_invalid_json_input():
    proc = run_raw(b"not json")
    assert proc.returncode == 0
    lines = proc.stdout.decode("utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"ok": False, "stdout": "", "error_type": "InvalidInput"}


def test_missing_code_key_is_invalid_input():
    proc = run_raw(json.dumps({"source": "print(1)"}).encode())
    assert json.loads(proc.stdout.decode("utf-8")) == {
        "ok": False,
        "stdout": "",
        "error_type": "InvalidInput",
    }


def test_system_exit_zero_is_ok():
    result = run_code(
        """
        import sys
        print("bye")
        sys.exit(0)
        """
    )
    assert result == {"ok": True, "stdout": "bye\n", "error_type": None}


def test_fd_level_writes_do_not_corrupt_result_line():
    result = run_code(
        """
        import os
        os.write(1, b"raw fd write\\n")
        print("kept")
        """
    )
    assert result["ok"] is True
    assert result["stdout"] == "kept\n"


def test_fakes_importable_from_other_cwd(tmp_path):
    result = run_code("from fakes import GenericFakeChatModel; print('ok')", cwd=tmp_path)
    assert result == {"ok": True, "stdout": "ok\n", "error_type": None}


def test_generic_fake_chat_model_scripted_reply():
    result = run_code(
        """
        from fakes import GenericFakeChatModel
        model = GenericFakeChatModel(messages=iter(["Hello from fake"]))
        print(model.invoke("hi").content)
        """
    )
    assert result == {"ok": True, "stdout": "Hello from fake\n", "error_type": None}


def test_tool_calling_fake_in_agent_flow():
    result = run_code(
        """
        from langchain.agents import create_agent
        from langchain_core.messages import AIMessage
        from langchain_core.tools import tool
        from fakes import ToolCallingFakeChatModel

        @tool
        def add(a: int, b: int) -> int:
            \"\"\"Add two integers.\"\"\"
            return a + b

        model = ToolCallingFakeChatModel(messages=iter([
            AIMessage(content="", tool_calls=[
                {"name": "add", "args": {"a": 2, "b": 3}, "id": "call_1"}
            ]),
            AIMessage(content="The sum is 5"),
        ]))
        agent = create_agent(model, tools=[add])
        out = agent.invoke({"messages": [{"role": "user", "content": "2+3?"}]})
        msgs = out["messages"]
        print(msgs[1].tool_calls[0]["name"])
        print(msgs[2].content)
        print(msgs[-1].content)
        """
    )
    assert result == {
        "ok": True,
        "stdout": "add\n5\nThe sum is 5\n",
        "error_type": None,
    }


def test_bind_tools_keeps_scripted_messages():
    result = run_code(
        """
        from langchain_core.messages import AIMessage
        from fakes import ToolCallingFakeChatModel

        model = ToolCallingFakeChatModel(messages=iter([
            AIMessage(content="", tool_calls=[{"name": "t", "args": {}, "id": "c1"}]),
        ]))
        bound = model.bind_tools([])
        print(bound.invoke("x").tool_calls[0]["id"])
        """
    )
    assert result == {"ok": True, "stdout": "c1\n", "error_type": None}


def test_langgraph_recursion_error_class_name():
    result = run_code(
        """
        from typing import TypedDict
        from langgraph.graph import StateGraph, START

        class S(TypedDict):
            n: int

        g = StateGraph(S)
        g.add_node("loop", lambda s: {"n": s["n"] + 1})
        g.add_edge(START, "loop")
        g.add_edge("loop", "loop")
        g.compile().invoke({"n": 0}, {"recursion_limit": 3})
        """
    )
    assert result["ok"] is False
    assert result["error_type"] == "GraphRecursionError"


def test_network_is_blocked():
    result = run_code(
        """
        import socket
        socket.create_connection(("example.com", 80), timeout=5)
        """
    )
    assert result == {"ok": False, "stdout": "", "error_type": "NetworkBlockedError"}


def test_raw_socket_connect_is_blocked():
    result = run_code(
        """
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 8000))
        """
    )
    assert result["error_type"] == "NetworkBlockedError"


def test_asyncio_connection_is_blocked():
    result = run_code(
        """
        import asyncio

        async def main():
            await asyncio.open_connection("127.0.0.1", 8000)

        asyncio.run(main())
        """
    )
    assert result["error_type"] == "NetworkBlockedError"


def test_asyncio_still_works():
    result = run_code(
        """
        import asyncio
        from fakes import GenericFakeChatModel

        async def main():
            model = GenericFakeChatModel(messages=iter(["async reply"]))
            msg = await model.ainvoke("hi")
            print(msg.content)

        asyncio.run(main())
        """
    )
    assert result == {"ok": True, "stdout": "async reply\n", "error_type": None}


# --- 격리(F-1, F-2): 감사 훅이 파일, 네트워크, 프로세스를 막는다 ---

BLOCKED = {"ok": False, "stdout": "", "error_type": "PermissionError"}


def work_with_secret(tmp_path: Path) -> Path:
    """작업 디렉토리 바로 위에 비밀 파일을 둔다. `../secret.txt`로 읽히면 안 된다."""
    (tmp_path / "secret.txt").write_text("DUMMY_SECRET=not-a-real-secret", encoding="utf-8")
    work = tmp_path / "work"
    work.mkdir()
    return work


def test_read_parent_of_workdir_is_blocked(tmp_path):
    work = work_with_secret(tmp_path)
    result = run_code("print(open('../secret.txt').read())", cwd=work)
    assert result == BLOCKED


def test_read_parent_with_absolute_path_and_os_open_is_blocked(tmp_path):
    work = work_with_secret(tmp_path)
    secret = str(tmp_path / "secret.txt")
    code = f"import os\nfd = os.open({secret!r}, os.O_RDONLY)\nprint(os.read(fd, 100))"
    assert run_code(code, cwd=work) == BLOCKED


def test_read_windows_ini_is_blocked():
    assert run_code("print(open(r'C:/Windows/win.ini').read())") == BLOCKED


def test_write_outside_workdir_is_blocked(tmp_path):
    work = work_with_secret(tmp_path)
    result = run_code("open('../PWNED.txt', 'w').write('x')", cwd=work)
    assert result == BLOCKED
    assert not (tmp_path / "PWNED.txt").exists()


def test_listdir_outside_workdir_is_blocked(tmp_path):
    work = work_with_secret(tmp_path)
    assert run_code("import os\nprint(os.listdir('..'))", cwd=work) == BLOCKED


def test_chdir_outside_workdir_is_blocked(tmp_path):
    work = work_with_secret(tmp_path)
    assert run_code("import os\nos.chdir('..')", cwd=work) == BLOCKED


def test_write_inside_workdir_works(tmp_path):
    code = """
        import os, pathlib, tempfile
        open('a.txt', 'w').write('hello')
        print(open('a.txt').read())
        os.mkdir('sub')
        pathlib.Path('sub/b.txt').write_text('b')
        print(sorted(os.listdir('.')))
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d, 'c.txt').write_text('c')
        os.remove('a.txt')
        """
    result = run_code(code, cwd=tmp_path)
    assert result == {"ok": True, "stdout": "hello\n['a.txt', 'sub']\n", "error_type": None}


def test_sqlite_connect_outside_workdir_is_blocked(tmp_path):
    work = work_with_secret(tmp_path)
    target = str(tmp_path / "quiz.db")
    code = f"import sqlite3\nsqlite3.connect({target!r}).execute('create table pwned(x)')"
    assert run_code(code, cwd=work) == BLOCKED
    assert not (tmp_path / "quiz.db").exists()


def test_subprocess_popen_is_blocked():
    code = "import subprocess\nsubprocess.Popen(['cmd', '/c', 'echo hi']).wait()"
    assert run_code(code) == BLOCKED


def test_os_system_is_blocked():
    assert run_code("import os\nos.system('echo hi')") == BLOCKED


def test_ctypes_native_call_is_blocked():
    code = "import ctypes\nprint(ctypes.windll.kernel32.GetTickCount())"
    assert run_code(code) == BLOCKED


def test_low_level_socket_connect_is_blocked():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.settimeout(0.5)
    port = listener.getsockname()[1]
    try:
        code = f"""
            import _socket
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            s.connect(("127.0.0.1", {port}))
            s.send(b"leak")
            """
        result = run_code(code)
        assert result == {"ok": False, "stdout": "", "error_type": "NetworkBlockedError"}
        try:
            conn, _ = listener.accept()
            conn.close()
            raise AssertionError("sandbox reached the listener")
        except TimeoutError:
            pass
    finally:
        listener.close()


def test_low_level_getaddrinfo_is_blocked():
    code = "import _socket\nprint(_socket.getaddrinfo('localhost', 80))"
    assert run_code(code)["error_type"] == "NetworkBlockedError"


def test_low_level_udp_sendto_is_blocked():
    code = """
        import _socket
        s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        s.sendto(b"leak", ("127.0.0.1", 9))
        """
    assert run_code(code)["error_type"] == "NetworkBlockedError"


def test_langgraph_tiny_graph_and_numpy_still_work():
    result = run_code(
        """
        from typing import TypedDict
        import numpy as np
        from langgraph.graph import StateGraph, START, END
        from langchain_text_splitters import CharacterTextSplitter
        from langchain_core.embeddings import DeterministicFakeEmbedding

        class S(TypedDict):
            n: int

        g = StateGraph(S)
        g.add_node("inc", lambda s: {"n": s["n"] + 1})
        g.add_edge(START, "inc")
        g.add_edge("inc", END)
        print(g.compile().invoke({"n": 1})["n"])
        print(int(np.arange(4).sum()))
        print(len(DeterministicFakeEmbedding(size=3).embed_query("x")))
        print(len(CharacterTextSplitter(chunk_size=5, chunk_overlap=0, separator=" ").split_text("aa bb cc")))
        """
    )
    assert result == {"ok": True, "stdout": "2\n6\n3\n2\n", "error_type": None}


def test_example_tool_agent_still_works():
    payload = (SANDBOX / "examples" / "tool_agent.json").read_bytes()
    with tempfile.TemporaryDirectory() as work:
        proc = run_raw(payload, cwd=Path(work))
    assert json.loads(proc.stdout.decode("utf-8")) == {"ok": True, "stdout": "The sum is 5\n", "error_type": None}
