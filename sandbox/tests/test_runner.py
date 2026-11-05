"""runner.py를 subprocess로 실행해 stdin JSON -> stdout JSON 한 줄 계약을 확인한다."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[1]
RUNNER = SANDBOX / "runner.py"


def run_raw(stdin: bytes, cwd: Path = SANDBOX) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        input=stdin,
        capture_output=True,
        cwd=cwd,
        timeout=120,
    )


def run_code(code: str, cwd: Path = SANDBOX) -> dict:
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
