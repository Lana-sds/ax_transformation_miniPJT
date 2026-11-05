# RecursiveCharacterTextSplitter

> **Class** in `langchain-text-splitters`

📖 [View in docs](https://reference.langchain.com/python/langchain-text-splitters/langchain_text_splitters/character/RecursiveCharacterTextSplitter)

Splitting text by recursively look at characters.

Recursively tries to split by different characters to find one
that works.

## Signature

```python
RecursiveCharacterTextSplitter(
    self,
    separators: list[str] | None = None,
    keep_separator: bool | Literal['start', 'end'] = True,
    is_separator_regex: bool = False,
    kwargs: Any = {},
)
```

## Extends

- `TextSplitter`

## Constructors

```python
__init__(
    self,
    separators: list[str] | None = None,
    keep_separator: bool | Literal['start', 'end'] = True,
    is_separator_regex: bool = False,
    kwargs: Any = {},
) -> None
```

| Name | Type |
|------|------|
| `separators` | `list[str] \| None` |
| `keep_separator` | `bool \| Literal['start', 'end']` |
| `is_separator_regex` | `bool` |
| `kwargs` | `Any` |


## Methods

- [`split_text()`](https://reference.langchain.com/python/langchain-text-splitters/langchain_text_splitters/character/RecursiveCharacterTextSplitter/split_text)
- [`from_language()`](https://reference.langchain.com/python/langchain-text-splitters/langchain_text_splitters/character/RecursiveCharacterTextSplitter/from_language)
- [`get_separators_for_language()`](https://reference.langchain.com/python/langchain-text-splitters/langchain_text_splitters/character/RecursiveCharacterTextSplitter/get_separators_for_language)

---

[View source on GitHub](https://github.com/langchain-ai/langchain/blob/e2db474707c90248f74b1398ea6f13883605f7e7/libs/text-splitters/langchain_text_splitters/character.py#L91)