# MultiServerMCPClient

> **Class** in `langchain-mcp-adapters`

📖 [View in docs](https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/client/MultiServerMCPClient)

Client for connecting to multiple MCP servers.

Loads LangChain-compatible tools, prompts and resources from MCP servers, and
retrieves server info from them.

## Signature

```python
MultiServerMCPClient(
    self,
    connections: dict[str, Connection] | None = None,
    *,
    callbacks: Callbacks | None = None,
    tool_interceptors: list[ToolCallInterceptor] | None = None,
    tool_name_prefix: bool = False,
    handle_tool_errors: bool = True,
)
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `connections` | `dict[str, Connection] \| None` | No | A `dict` mapping server names to connection configurations. If `None`, no initial connections are established. (default: `None`) |
| `callbacks` | `Callbacks \| None` | No | Optional callbacks for handling notifications and events. (default: `None`) |
| `tool_interceptors` | `list[ToolCallInterceptor] \| None` | No | Optional list of tool call interceptors for modifying requests and responses. (default: `None`) |
| `tool_name_prefix` | `bool` | No | If `True`, tool names are prefixed with the server name using an underscore separator (e.g., `"weather_search"` instead of `"search"`). This helps avoid conflicts when multiple servers have tools with the same name. Defaults to `False`. (default: `False`) |
| `handle_tool_errors` | `bool` | No | If `True` (default), an MCP tool execution error (`CallToolResult(isError=True)`) is returned to the model as a `ToolMessage` with `status="error"` so the agent can self-correct instead of crashing the run. If `False`, a `ToolException` is raised instead (legacy behavior). Transport/session failures and content-conversion errors (e.g. unsupported audio content) always raise regardless of this setting; only MCP execution errors (`isError=True`) are governed by it. (default: `True`) |

## Constructors

```python
__init__(
    self,
    connections: dict[str, Connection] | None = None,
    *,
    callbacks: Callbacks | None = None,
    tool_interceptors: list[ToolCallInterceptor] | None = None,
    tool_name_prefix: bool = False,
    handle_tool_errors: bool = True,
) -> None
```

| Name | Type |
|------|------|
| `connections` | `dict[str, Connection] \| None` |
| `callbacks` | `Callbacks \| None` |
| `tool_interceptors` | `list[ToolCallInterceptor] \| None` |
| `tool_name_prefix` | `bool` |
| `handle_tool_errors` | `bool` |


## Properties

- `connections`
- `callbacks`
- `tool_interceptors`
- `tool_name_prefix`
- `handle_tool_errors`

## Methods

- [`session()`](https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/client/MultiServerMCPClient/session)
- [`get_tools()`](https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/client/MultiServerMCPClient/get_tools)
- [`get_server_info()`](https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/client/MultiServerMCPClient/get_server_info)
- [`get_prompt()`](https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/client/MultiServerMCPClient/get_prompt)
- [`get_resources()`](https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/client/MultiServerMCPClient/get_resources)

---

[View source on GitHub](https://github.com/langchain-ai/langchain-mcp-adapters/blob/cc0f2843fd5becf2cdb641c910533c3747c3b1ef/langchain_mcp_adapters/client.py#L48)