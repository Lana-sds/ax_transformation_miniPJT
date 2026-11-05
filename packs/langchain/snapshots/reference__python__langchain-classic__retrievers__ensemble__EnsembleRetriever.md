# EnsembleRetriever

> **Class** in `langchain-classic`

📖 [View in docs](https://reference.langchain.com/python/langchain-classic/langchain_classic/retrievers/ensemble/EnsembleRetriever)

Retriever that ensembles the multiple retrievers.

It uses a rank fusion.

## Signature

```python
EnsembleRetriever()
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `retrievers` | `unknown` | Yes | A list of retrievers to ensemble. |
| `weights` | `unknown` | Yes | A list of weights corresponding to the retrievers. Defaults to equal weighting for all retrievers. |
| `c` | `unknown` | Yes | A constant added to the rank, controlling the balance between the importance of high-ranked items and the consideration given to lower-ranked items. |
| `id_key` | `unknown` | Yes | The key in the document's metadata used to determine unique documents. If not specified, page_content is used. |

## Extends

- `BaseRetriever`

## Properties

- `retrievers`
- `weights`
- `c`
- `id_key`
- `config_specs`

## Methods

- [`invoke()`](https://reference.langchain.com/python/langchain-classic/langchain_classic/retrievers/ensemble/EnsembleRetriever/invoke)
- [`ainvoke()`](https://reference.langchain.com/python/langchain-classic/langchain_classic/retrievers/ensemble/EnsembleRetriever/ainvoke)
- [`rank_fusion()`](https://reference.langchain.com/python/langchain-classic/langchain_classic/retrievers/ensemble/EnsembleRetriever/rank_fusion)
- [`arank_fusion()`](https://reference.langchain.com/python/langchain-classic/langchain_classic/retrievers/ensemble/EnsembleRetriever/arank_fusion)
- [`weighted_reciprocal_rank()`](https://reference.langchain.com/python/langchain-classic/langchain_classic/retrievers/ensemble/EnsembleRetriever/weighted_reciprocal_rank)

---

[View source on GitHub](https://github.com/langchain-ai/langchain/blob/5dcec1858191a6b54cd843dd8e54d856e2e007cc/libs/langchain/langchain_classic/retrievers/ensemble.py#L53)