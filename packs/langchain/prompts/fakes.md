### Sandbox fakes

The sandbox runs each program offline with `langchain`, `langchain-core` and `langgraph` installed. Network access raises `NetworkBlockedError`. The module `fakes` exports two models:

- `GenericFakeChatModel`: replies with scripted messages in order.
- `ToolCallingFakeChatModel`: same, plus `bind_tools(...)` that returns the same model, so it works with `create_agent` and `ToolNode`. Scripted tool calls need an `id`.

`messages` must be an iterator: wrap the list in `iter([...])`.

```python
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from fakes import GenericFakeChatModel, ToolCallingFakeChatModel

print(GenericFakeChatModel(messages=iter(["Hello"])).invoke("hi").content)  # prints: Hello

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

model = ToolCallingFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[{"name": "add", "args": {"a": 2, "b": 3}, "id": "call_1"}]),
    AIMessage(content="The sum is 5"),
]))
out = create_agent(model, tools=[add]).invoke({"messages": [{"role": "user", "content": "2+3?"}]})
print(out["messages"][-1].content)  # prints: The sum is 5
```
