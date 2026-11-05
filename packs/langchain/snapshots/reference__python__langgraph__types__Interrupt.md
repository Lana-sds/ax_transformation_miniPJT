# Interrupt

> **Class** in `langgraph`

📖 [View in docs](https://reference.langchain.com/python/langgraph/types/Interrupt)

Information about an interrupt that occurred in a node.

!!! version-added "Added in version 0.2.24"

!!! version-changed "Changed in version v0.4.0"
    * `interrupt_id` was introduced as a property

!!! version-changed "Changed in version v0.6.0"

    The following attributes have been removed:

    * `ns`
    * `when`
    * `resumable`
    * `interrupt_id`, deprecated in favor of `id`

## Signature

```python
Interrupt(
    self,
    value: Any,
    id: str = _DEFAULT_INTERRUPT_ID,
    *,
    response_schema: type[ResponseT] | dict[str, Any] | None = None,
    deprecated_kwargs: Unpack[DeprecatedKwargs] = {},
)
```

## Extends

- `Generic[ResponseT]`

## Constructors

```python
__init__(
    self,
    value: Any,
    id: str = _DEFAULT_INTERRUPT_ID,
    *,
    response_schema: type[ResponseT] | dict[str, Any] | None = None,
    deprecated_kwargs: Unpack[DeprecatedKwargs] = {},
) -> None
```

| Name | Type |
|------|------|
| `value` | `Any` |
| `id` | `str` |
| `response_schema` | `type[ResponseT] \| dict[str, Any] \| None` |
| `deprecated_kwargs` | `Unpack[DeprecatedKwargs]` |


## Properties

- `value`
- `id`
- `response_schema`
- `interrupt_id`

## Methods

- [`from_ns()`](https://reference.langchain.com/python/langgraph/types/Interrupt/from_ns)

---

[View source on GitHub](https://github.com/langchain-ai/langgraph/blob/5bd231cbfd913e05ebc662f519eb9a655bc766df/libs/langgraph/langgraph/types.py#L582)