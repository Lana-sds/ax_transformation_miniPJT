# MCPAdapter

> **Class** in `langchain`

📖 [View in docs](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter)

Adapt an MCP target into LangChain tools.

`MCPAdapter` uses FastMCP for protocol negotiation and connection management,
then converts discovered MCP tools into asynchronous LangChain tools. The
resulting tools can be passed directly to `create_agent`.

Transport inference is delegated to `fastmcp.Client`, so a target may be a URL,
a local script path (launched over stdio), an in-process server, or an already
constructed client.

!!! warning "A string target must be an http(s) URL"

    `fastmcp.Client` resolves a string by testing it as a filesystem path
    before testing it as a URL, so a string naming an existing `.py` or `.js`
    file launches that file as a subprocess. Because strings are the form a
    target most often arrives in from configuration or from a model,
    `MCPAdapter` rejects one that is not an `http` or `https` URL rather than
    let it select local execution. Reach a local server through `Path`, a
    `fastmcp` transport, or an `MCPConfig`, all of which say so explicitly.

A server that needs input mid-call is answered with a LangGraph
`interrupt()`, so a human answers and the run resumes — see
`langchain.mcp.elicitation`. This is the default: the adapter arms every
client it builds to advertise the elicitation capability and drives the
interrupt loop on each call. A server that never asks for input is
unaffected, since the loop only runs when the server returns a request.

A pre-built client (or `ClientGroup`) that already carries its own
elicitation handler is honored rather than overridden: its handler keeps
answering, and the adapter leaves the client as the caller built it. Only a
client with no handler is armed, and it is cloned first so the caller's own
object is never mutated.

## Signature

```python
MCPAdapter(
    self,
    target: MCPAdapterTarget,
)
```

## Description

**Example:**

```python
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter

async with MCPAdapter("https://example.com/mcp") as adapter:
    agent = create_agent("anthropic:claude-sonnet-5", await adapter.list_tools())
    result = await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `target` | `MCPAdapterTarget` | Yes | MCP target accepted by `fastmcp.Client`, including an existing FastMCP client. A `str` must be an `http`/`https` URL. |

## Constructors

```python
__init__(
    self,
    target: MCPAdapterTarget,
) -> None
```

| Name | Type |
|------|------|
| `target` | `MCPAdapterTarget` |


## Properties

- `client`

## Methods

- [`list_tools()`](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter/list_tools)

---

[View source on GitHub](https://github.com/langchain-ai/langchain/blob/5dcec1858191a6b54cd843dd8e54d856e2e007cc/libs/langchain_v1/langchain/mcp/adapter.py#L125)