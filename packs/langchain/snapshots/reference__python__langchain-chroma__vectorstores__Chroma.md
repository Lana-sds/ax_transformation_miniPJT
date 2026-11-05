# Chroma

> **Class** in `langchain-chroma`

📖 [View in docs](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma)

Chroma vector store integration.

## Signature

```python
Chroma(
    self,
    collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
    embedding_function: Embeddings | None = None,
    persist_directory: str | None = None,
    host: str | None = None,
    port: int | None = None,
    headers: dict[str, str] | None = None,
    chroma_cloud_api_key: str | None = None,
    tenant: str | None = None,
    database: str | None = None,
    client_settings: chromadb.config.Settings | None = None,
    collection_metadata: dict | None = None,
    collection_configuration: CreateCollectionConfiguration | None = None,
    client: chromadb.ClientAPI | None = None,
    relevance_score_fn: Callable[[float], float] | None = None,
    create_collection_if_not_exists: bool | None = True,
    *,
    ssl: bool = False,
)
```

## Description

**Setup:**

Install `chromadb`, `langchain-chroma` packages:

```bash
pip install -qU chromadb langchain-chroma
```

Key init args — indexing params:
    collection_name:
        Name of the collection.
    embedding_function:
        Embedding function to use.

Key init args — client params:
    client:
        Chroma client to use.
    client_settings:
        Chroma client settings.
    persist_directory:
        Directory to persist the collection.
    host:
        Hostname of a deployed Chroma server.
    port:
        Connection port for a deployed Chroma server. Default is 8000.
    ssl:
        Whether to establish an SSL connection with a deployed Chroma server. Default is False.
    headers:
        HTTP headers to send to a deployed Chroma server.
    chroma_cloud_api_key:
        Chroma Cloud API key.
    tenant:
        Tenant ID. Required for Chroma Cloud connections. Default is 'default_tenant' for local Chroma servers.
    database:
        Database name. Required for Chroma Cloud connections. Default is 'default_database'.

**Instantiate:**

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vector_store = Chroma(
    collection_name="foo",
    embedding_function=OpenAIEmbeddings(),
    # other params...
)
```

**Add Documents:**

```python
from langchain_core.documents import Document

document_1 = Document(page_content="foo", metadata={"baz": "bar"})
document_2 = Document(page_content="thud", metadata={"bar": "baz"})
document_3 = Document(page_content="i will be deleted :(")

documents = [document_1, document_2, document_3]
ids = ["1", "2", "3"]
vector_store.add_documents(documents=documents, ids=ids)
```

**Update Documents:**

```python
updated_document = Document(
    page_content="qux",
    metadata={"bar": "baz"},
)

vector_store.update_documents(ids=["1"], documents=[updated_document])
```

**Delete Documents:**

```python
vector_store.delete(ids=["3"])
```

**Search:**

```python
results = vector_store.similarity_search(query="thud", k=1)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")
```
```python
*thud[{"baz": "bar"}]
```

**Search with filter:**

```python
results = vector_store.similarity_search(
    query="thud", k=1, filter={"baz": "bar"}
)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")
```
```python
*foo[{"baz": "bar"}]
```

**Search with score:**

```python
results = vector_store.similarity_search_with_score(query="qux", k=1)
for doc, score in results:
    print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")
```
```python
* [SIM=0.000000] qux [{'bar': 'baz', 'baz': 'bar'}]
```

**Async:**

```python
# add documents
# await vector_store.aadd_documents(documents=documents, ids=ids)

# delete documents
# await vector_store.adelete(ids=["3"])

# search
# results = vector_store.asimilarity_search(query="thud",k=1)

# search with score
results = await vector_store.asimilarity_search_with_score(query="qux", k=1)
for doc, score in results:
    print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")
```

```python
* [SIM=0.335463] foo [{'baz': 'bar'}]
```

**Use as Retriever:**

```python
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 1, "fetch_k": 2, "lambda_mult": 0.5},
)
retriever.invoke("thud")
```

```python
[Document(metadata={"baz": "bar"}, page_content="thud")]
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `collection_name` | `str` | No | Name of the collection to create. (default: `_LANGCHAIN_DEFAULT_COLLECTION_NAME`) |
| `embedding_function` | `Embeddings \| None` | No | Embedding class object. Used to embed texts. (default: `None`) |
| `persist_directory` | `str \| None` | No | Directory to persist the collection. (default: `None`) |
| `host` | `str \| None` | No | Hostname of a deployed Chroma server. (default: `None`) |
| `port` | `int \| None` | No | Connection port for a deployed Chroma server. Default is 8000. (default: `None`) |
| `ssl` | `bool` | No | Whether to establish an SSL connection with a deployed Chroma server.     Default is False. (default: `False`) |
| `headers` | `dict[str, str] \| None` | No | HTTP headers to send to a deployed Chroma server. (default: `None`) |
| `chroma_cloud_api_key` | `str \| None` | No | Chroma Cloud API key. (default: `None`) |
| `tenant` | `str \| None` | No | Tenant ID. Required for Chroma Cloud connections.     Default is 'default_tenant' for local Chroma servers. (default: `None`) |
| `database` | `str \| None` | No | Database name. Required for Chroma Cloud connections.     Default is 'default_database'. (default: `None`) |
| `client_settings` | `chromadb.config.Settings \| None` | No | Chroma client settings (default: `None`) |
| `collection_metadata` | `dict \| None` | No | Collection configurations. (default: `None`) |
| `collection_configuration` | `CreateCollectionConfiguration \| None` | No | Index configuration for the collection. (default: `None`) |
| `client` | `chromadb.ClientAPI \| None` | No | Chroma client. Documentation:     https://docs.trychroma.com/reference/python/client (default: `None`) |
| `relevance_score_fn` | `Callable[[float], float] \| None` | No | Function to calculate relevance score from distance.     Used only in `similarity_search_with_relevance_scores` (default: `None`) |
| `create_collection_if_not_exists` | `bool \| None` | No | Whether to create collection     if it doesn't exist. Defaults to `True`. (default: `True`) |

## Extends

- `VectorStore`

## Constructors

```python
__init__(
    self,
    collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
    embedding_function: Embeddings | None = None,
    persist_directory: str | None = None,
    host: str | None = None,
    port: int | None = None,
    headers: dict[str, str] | None = None,
    chroma_cloud_api_key: str | None = None,
    tenant: str | None = None,
    database: str | None = None,
    client_settings: chromadb.config.Settings | None = None,
    collection_metadata: dict | None = None,
    collection_configuration: CreateCollectionConfiguration | None = None,
    client: chromadb.ClientAPI | None = None,
    relevance_score_fn: Callable[[float], float] | None = None,
    create_collection_if_not_exists: bool | None = True,
    *,
    ssl: bool = False,
) -> None
```

| Name | Type |
|------|------|
| `collection_name` | `str` |
| `embedding_function` | `Embeddings \| None` |
| `persist_directory` | `str \| None` |
| `host` | `str \| None` |
| `port` | `int \| None` |
| `headers` | `dict[str, str] \| None` |
| `chroma_cloud_api_key` | `str \| None` |
| `tenant` | `str \| None` |
| `database` | `str \| None` |
| `client_settings` | `chromadb.config.Settings \| None` |
| `collection_metadata` | `dict \| None` |
| `collection_configuration` | `CreateCollectionConfiguration \| None` |
| `client` | `chromadb.ClientAPI \| None` |
| `relevance_score_fn` | `Callable[[float], float] \| None` |
| `create_collection_if_not_exists` | `bool \| None` |
| `ssl` | `bool` |


## Properties

- `override_relevance_score_fn`
- `embeddings`

## Methods

- [`encode_image()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/encode_image)
- [`fork()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/fork)
- [`add_images()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/add_images)
- [`add_texts()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/add_texts)
- [`hybrid_search()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/hybrid_search)
- [`similarity_search()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/similarity_search)
- [`similarity_search_by_vector()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/similarity_search_by_vector)
- [`similarity_search_by_vector_with_relevance_scores()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/similarity_search_by_vector_with_relevance_scores)
- [`similarity_search_with_score()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/similarity_search_with_score)
- [`similarity_search_with_vectors()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/similarity_search_with_vectors)
- [`similarity_search_by_image()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/similarity_search_by_image)
- [`similarity_search_by_image_with_relevance_score()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/similarity_search_by_image_with_relevance_score)
- [`max_marginal_relevance_search_by_vector()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/max_marginal_relevance_search_by_vector)
- [`max_marginal_relevance_search()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/max_marginal_relevance_search)
- [`delete_collection()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/delete_collection)
- [`reset_collection()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/reset_collection)
- [`get()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/get)
- [`get_by_ids()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/get_by_ids)
- [`update_document()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/update_document)
- [`update_documents()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/update_documents)
- [`from_texts()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/from_texts)
- [`from_documents()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/from_documents)
- [`delete()`](https://reference.langchain.com/python/langchain-chroma/langchain_chroma/vectorstores/Chroma/delete)

---

[View source on GitHub](https://github.com/langchain-ai/langchain/blob/bc232e6d036dd1369cdf3511e94bce93a10284f3/libs/partners/chroma/langchain_chroma/vectorstores.py#L155)