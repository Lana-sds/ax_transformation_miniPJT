# load_mcp_tools

> **Function** in `langchain-mcp-adapters`

📖 [View in docs](https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/tools/load_mcp_tools)

Load all available MCP tools and convert them to LangChain [tools](https://docs.langchain.com/oss/python/langchain/tools).

## Signature

```python
load_mcp_tools(
    session: ClientSession | None,
    *,
    connection: Connection | None = None,
    callbacks: Callbacks | None = None,
    tool_interceptors: list[ToolCallInterceptor] | None = None,
    server_name: str | None = None,
    tool_name_prefix: bool = False,
    handle_tool_errors: bool = True,
) -> list[BaseTool]
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `session` | `ClientSession \| None` | Yes | The MCP client session. If `None`, connection must be provided. |
| `connection` | `Connection \| None` | No | Connection config to create a new session if session is `None`. (default: `None`) |
| `callbacks` | `Callbacks \| None` | No | Optional `Callbacks` for handling notifications and events. (default: `None`) |
| `tool_interceptors` | `list[ToolCallInterceptor] \| None` | No | Optional list of interceptors for tool call processing. (default: `None`) |
| `server_name` | `str \| None` | No | Name of the server these tools belong to. (default: `None`) |
| `tool_name_prefix` | `bool` | No | If `True` and `server_name` is provided, tool names will be prefixed w/ server name (e.g., `"weather_search"` instead of `"search"`). (default: `False`) |
| `handle_tool_errors` | `bool` | No | If `True` (default), an MCP tool execution error (`CallToolResult(isError=True)`) is returned to the model as a `ToolMessage` with `status="error"` so the agent can self-correct instead of crashing the run. If `False`, a `ToolException` is raised instead (legacy behavior). Transport/session failures and content-conversion errors (e.g. unsupported audio content) always raise regardless of this setting; only MCP execution errors (`isError=True`) are governed by it. (default: `True`) |

## Returns

`list[BaseTool]`

List of LangChain [tools](https://docs.langchain.com/oss/python/langchain/tools).
Tool annotations are returned as part of the tool metadata object.

---

[View source on GitHub](https://github.com/langchain-ai/langchain-mcp-adapters/blob/cc0f2843fd5becf2cdb641c910533c3747c3b1ef/langchain_mcp_adapters/tools.py#L539)