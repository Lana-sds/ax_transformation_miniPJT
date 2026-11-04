# 공식 문서 페이지 허용 목록 (GR-2)

상태: 확정(2026-11-04, 사용자 검토 완료)
조회 날짜: 2026-11-04. 모든 행을 이 날짜에 조회했다.
조회 수단: `docs-langchain` MCP(`.mdx` 원문을 `head`, `rg`로 열어 확인), `reference-langchain` MCP(`search_api`, `get_symbol`)
기록: [02-docs-mcp.md](../../dev-process/02-spec-design/02-docs-mcp.md)
요구사항: [requirements.md](../../01-requirements/output/requirements.md) CR-1, GR-1~GR-4

## 읽는 법

- 경로: 문서는 `docs.langchain.com` 아래 URL 경로이며 `.mdx`를 뺐다. API 레퍼런스는 전체 URL이다. Python 문서만 쓴다.
- 종류: `docs`(문서 페이지), `api-ref`(API 레퍼런스)
- 상태:
  - `확인`: 원문을 열어 주제 내용을 봤다.
  - `근접`: 주제 이름이 문서에 없고 가장 가까운 내용만 있다. 이 행을 근거로 쓰는 문제는 문서가 그 이름으로 패턴을 정의한다고 쓰면 안 된다.
  - `없음`: 허용 목록에 넣을 페이지가 없다. 이 주제는 출제하지 않는다(requirements CR-9 "허용 목록에 없는 내용").
- 페이지 스냅샷 파일과 파이프라인이 읽는 데이터 파일은 3단계에서 이 표로부터 코드 쪽에 만든다([design.md](design.md) 4.3).

## RAG (day2)

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 1 | 문서 로드 | `/oss/python/integrations/document_loaders` | docs | 확인 | "Document loader integrations", "## Interface" |
| 1 | 문서 로드 | `/oss/python/langchain/knowledge-base` | docs | 확인 | "## Load and split a PDF"(569행) |
| 2 | 청킹·메타데이터 | `/oss/python/langchain/knowledge-base` | docs | 확인 | `RecursiveCharacterTextSplitter`, `add_start_index=True`(601~609행) |
| 2 | 청킹·메타데이터 | `/oss/python/integrations/splitters` | docs | 확인 | "# Text splitter integrations" |
| 2 | 청킹·메타데이터 | https://reference.langchain.com/python/langchain-text-splitters/character/RecursiveCharacterTextSplitter | api-ref | 확인 | `search_api` 결과 |
| 3 | 임베딩 | `/oss/python/integrations/embeddings` | docs | 확인 | "### How it works", "### Similarity metrics" |
| 3 | 임베딩 | `/oss/python/langchain/knowledge-base` | docs | 확인 | "## Generate embeddings"(96행) |
| 4 | Chroma | `/oss/python/langchain/knowledge-base` | docs | 확인 | Chroma 탭, `from langchain_chroma import Chroma` |
| 4 | Chroma | `/oss/python/integrations/vectorstores` | docs | 확인 | Chroma 항목, `pip install langchain-chroma` |
| 4 | Chroma | https://reference.langchain.com/python/langchain-chroma/vectorstores/Chroma | api-ref | 확인 | `search_api` 결과 |
| 5 | Retriever | `/oss/python/langchain/knowledge-base` | docs | 확인 | "## Use retrievers"(746행), `as_retriever`, `search_type` |
| 5 | Retriever | `/oss/python/integrations/retrievers` | docs | 확인 | "## Bring-your-own documents" |
| 6 | 하이브리드 검색 | `/oss/python/integrations/embeddings` | docs | 확인 | "#### Sparse and hybrid retrieval"(159행), dense + BM25 |
| 6 | 하이브리드 검색 | https://reference.langchain.com/python/langchain-classic/retrievers/ensemble/EnsembleRetriever | api-ref | 확인 | `search_api` 결과. 패키지 `langchain_classic` |
| 7 | 재랭킹 | https://reference.langchain.com/python/langchain-classic/retrievers/contextual_compression/ContextualCompressionRetriever | api-ref | 확인 | `search_api` 결과. 패키지 `langchain_classic` |
| 7 | 재랭킹 | `/oss/python/integrations/retrievers` | docs | 근접 | 재랭커 통합 목록만 있다(144~178행). 설명 문장 없음 |

## LangGraph 기초 (day3)

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 1 | State·노드·엣지 | `/oss/python/langgraph/graph-api` | docs | 확인 | "### StateGraph", "## State", "## Nodes", "## Edges" |
| 1 | State·노드·엣지 | `/oss/python/langgraph/graph-api-state` | docs | 확인 | "## Define state" |
| 2 | 조건부 엣지 | `/oss/python/langgraph/graph-api` | docs | 확인 | "### Conditional edges"(334행) |
| 2 | 조건부 엣지 | `/oss/python/langgraph/graph-api-control-flow` | docs | 확인 | "### Conditional branching", `add_conditional_edges` |
| 3 | 사이클 | `/oss/python/langgraph/graph-api-control-flow` | docs | 확인 | "## Create and control loops", "### Impose a recursion limit" |
| 3 | 사이클 | `/oss/python/langgraph/graph-api` | docs | 확인 | "### Recursion limit"(549행) |
| 4 | `add_messages` 리듀서 | `/oss/python/langgraph/graph-api-state` | docs | 확인 | "## Process state updates with reducers", "### MessagesState" |
| 4 | `add_messages` 리듀서 | `/oss/python/langgraph/graph-api` | docs | 확인 | "### Reducers", "#### MessagesState" |
| 5 | ReAct | `/oss/python/langchain/agents` | docs | 근접 | "a model calling tools in a loop". "ReAct"라는 이름은 쓰지 않는다 |
| 6 | LangSmith Studio | `/langsmith/studio` | docs | 확인 | "# LangSmith Studio" |
| 6 | LangSmith Studio | `/oss/python/langgraph/studio` | docs | 확인 | "# LangSmith Studio", 로컬 에이전트 시각화 |

## Tool · MCP (day4)

MCP 행(#4, #5, #6의 `mcp/tools`)은 개념·설계 문제에만 쓴다. MCP 코드형 문제는 내지 않는다([design.md](design.md) 6.1 슬롯 계획, 9장 D-9).

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 1 | `@tool` | `/oss/python/langchain/tools` | docs | 확인 | "### Basic tool definition", `@tool`(17행) |
| 2 | ToolNode 병렬·에러 처리 | `/oss/python/langgraph/workflows-agents` | docs | 확인 | "### ToolNode"(1111행), 병렬 실행 |
| 2 | ToolNode 병렬·에러 처리 | https://reference.langchain.com/python/langgraph.prebuilt/tool_node/ToolNode | api-ref | 확인 | `search_api` 결과. "parallel execution, error handling" |
| 3 | FastMCP 서버 | - | - | 없음 | Python 문서에 서버 작성 페이지가 없다. FastMCP는 `MCPAdapter`의 대상으로만 언급된다 |
| 4 | MCP 클라이언트 | `/oss/python/langchain/mcp` | docs | 확인 | "## Transports", "## Quickstart". `langchain.mcp.MCPAdapter` 기준 |
| 4 | MCP 클라이언트 | `/oss/python/langchain/mcp/connections` | docs | 확인 | "## Connection lifecycle", "## Multiple servers" |
| 4 | MCP 클라이언트 | https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter | api-ref | 확인 | `search_api` 결과 |
| 5 | `langchain-mcp-adapters` | `/oss/python/migrate/langchain-mcp-adapters` | docs | 확인 | "`MultiServerMCPClient` is collapsed into a single `MCPAdapter` class" |
| 5 | `langchain-mcp-adapters` | https://reference.langchain.com/python/langchain-mcp-adapters/client/MultiServerMCPClient | api-ref | 확인 | `search_api` 결과. 레퍼런스가 어느 패키지 버전 기준인지 미확인 |
| 5 | `langchain-mcp-adapters` | https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/tools/load_mcp_tools | api-ref | 확인 | `get_symbol` 결과. `handle_tool_errors: bool = True` |
| 6 | 장애 주입 | `/oss/python/langgraph/fault-tolerance` | docs | 확인 | "## Retries", "## Retry boundaries and idempotency" |
| 6 | 장애 주입 | `/oss/python/langchain/middleware/built-in` | docs | 확인 | "### Tool retry", `ToolRetryMiddleware` |
| 6 | 장애 주입 | `/oss/python/langchain/mcp/tools` | docs | 확인 | "### Errors", `isError`가 `ToolMessage status="error"`로 |

## 미들웨어 · HITL · 가드레일 (day5)

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 1 | 훅 호출 순서 | `/oss/python/langchain/middleware/custom` | docs | 확인 | "## Hooks", "## Execution order"(557행) |
| 1 | 훅 호출 순서 | `/oss/python/langchain/middleware/overview` | docs | 확인 | "## The agent loop" |
| 2 | 로깅·마스킹·요약 미들웨어 | `/oss/python/langchain/middleware/built-in` | docs | 확인 | "### Summarization", "### PII detection". 로깅 전용 내장 미들웨어는 없다 |
| 2 | 로깅·마스킹·요약 미들웨어 | `/oss/python/langchain/middleware/custom` | docs | 확인 | 로깅 용도 커스텀 훅 예시 |
| 3 | checkpointer·`thread_id` | `/oss/python/langchain/short-term-memory` | docs | 확인 | `checkpointer` 지정, `thread_id` 설정 예시 |
| 3 | checkpointer·`thread_id` | `/oss/python/langgraph/persistence` | docs | 확인 | "Checkpointer vs. store" |
| 4 | `interrupt()`·`Command(resume)` | `/oss/python/langgraph/interrupts` | docs | 확인 | "## Pause using `interrupt`", "## Resuming interrupts" |
| 4 | `interrupt()`·`Command(resume)` | `/oss/python/langchain/human-in-the-loop` | docs | 확인 | "Interrupt decision types", "Responding to interrupts" |
| 5 | 가드레일 | `/oss/python/langchain/guardrails` | docs | 확인 | "### PII detection", "## Custom guardrails" |

## 멀티 에이전트 (day6)

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 1 | Supervisor | `/oss/python/langchain/multi-agent/subagents` | docs | 확인 | "main agent (often referred to as a **supervisor**)" |
| 1 | Supervisor | `/oss/python/langchain/multi-agent/subagents-personal-assistant` | docs | 확인 | "The **supervisor pattern** is a multi-agent architecture" |
| 1 | Supervisor | `/oss/python/migrate/langgraph-supervisor` | docs | 확인 | `langgraph-supervisor`는 더 이상 관리하지 않음, `create_supervisor`에서 `create_agent`로 |
| 2 | handoff | `/oss/python/langchain/multi-agent/handoffs` | docs | 확인 | "# Handoffs" |
| 2 | handoff | `/oss/python/langchain/multi-agent/handoffs-customer-support` | docs | 확인 | "# Build customer support with handoffs" |
| 3 | 계층 구조 | `/oss/python/langgraph/use-subgraphs` | docs | 근접 | 부모 그래프와 서브그래프. "hierarchical"이라는 표현은 멀티 에이전트 문서에 없다 |
| 4 | 서브 Agent 설계 | `/oss/python/langchain/multi-agent/subagents` | docs | 확인 | "provides context isolation" |
| 4 | 서브 Agent 설계 | `/oss/python/langchain/multi-agent/index` | docs | 확인 | "strong context isolation but... repeated model calls"(209행) |
| 5 | 라우팅 검증 | `/oss/python/langchain/multi-agent/router` | docs | 확인 | "# Router", "Stateless vs. stateful" |
| 5 | 라우팅 검증 | `/oss/python/langchain/multi-agent/router-knowledge-base` | docs | 확인 | "Build the router workflow" |
| 5 | 라우팅 검증 | `/oss/python/langchain/test/evals` | docs | 근접 | 궤적 매칭 평가. 라우팅 검증 전용 문서는 없다 |

## 운영 품질 (day7)

| # | 주제 | 경로 | 종류 | 상태 | 확인 |
| --- | --- | --- | --- | --- | --- |
| 1 | Plan-and-Execute | `/oss/python/langgraph/workflows-agents` | docs | 근접 | "## Orchestrator-worker"(550행), planner. "Plan-and-Execute"라는 이름은 Python 문서에 없다 |
| 1 | Plan-and-Execute | `/oss/python/deepagents/overview` | docs | 근접 | "### Task planning", `write_todos` |
| 2 | 단기·장기 기억 | `/oss/python/langchain/short-term-memory` | docs | 확인 | "# Short-term memory" |
| 2 | 단기·장기 기억 | `/oss/python/langchain/long-term-memory` | docs | 확인 | "# Long-term memory", "Memory storage" |
| 2 | 단기·장기 기억 | `/oss/python/concepts/memory` | docs | 확인 | thread 범위와 cross-thread namespace |
| 3 | 콜백 관측 | `/oss/python/langgraph/observability` | docs | 확인 | `.with_config({'callbacks': [tracer]})`(119행) |
| 3 | 콜백 관측 | `/langsmith/trace-with-langchain` | docs | 확인 | `LangChainTracer`를 callback으로(176행) |
| 3 | 콜백 관측 | `/oss/python/langchain/observability` | docs | 확인 | "LangSmith Observability" |
| 3 | 콜백 관측 | https://reference.langchain.com/python/langchain-core/callbacks/base/BaseCallbackHandler | api-ref | 확인 | `search_api` 결과 |
| 4 | LLM-as-judge | `/langsmith/evaluation-concepts` | docs | 확인 | "#### LLM-as-judge"(212행) |
| 4 | LLM-as-judge | `/langsmith/llm-as-judge` | docs | 확인 | "How to define an LLM-as-a-judge evaluator" |
| 4 | LLM-as-judge | `/oss/python/langchain/test/evals` | docs | 확인 | "## LLM-as-judge evaluator"(182행) |
| 5 | 통합 점검 | `/oss/python/langchain/test/integration-testing` | docs | 확인 | "# Integration testing", `@pytest.mark.integration` |
| 5 | 통합 점검 | `/oss/python/langchain/test/evals` | docs | 확인 | "# Agent Evals" |

## 요약

| 버킷 | 주제 | 확인 | 근접만 | 없음 |
| --- | --- | --- | --- | --- |
| RAG | 7 | 7 | 0 | 0 |
| LangGraph 기초 | 6 | 5 | 1 (ReAct) | 0 |
| Tool · MCP | 6 | 5 | 0 | 1 (FastMCP 서버) |
| 미들웨어 · HITL · 가드레일 | 5 | 5 | 0 | 0 |
| 멀티 에이전트 | 5 | 4 | 1 (계층 구조) | 0 |
| 운영 품질 | 5 | 4 | 1 (Plan-and-Execute) | 0 |
| 합계 | 34 | 30 | 3 | 1 |

- 재랭킹은 api-ref로 확인했다. 문서 페이지는 목록만 있어 근접이다.
- api-ref로만 확인한 주제는 없다. 하이브리드 검색과 재랭킹은 문서 페이지도 있다.
- 쓰지 않기로 한 경로: `create_react_agent`(langgraph.prebuilt, deprecated), `create_supervisor` 레퍼런스(패키지 관리 중단), `@tool` 레퍼런스(`search_api`로 확인 안 됨), `/oss/python/integrations/retrievers/cohere-reranker`(파일 없음), `/oss/python/deepagents/retrieval`의 Hybrid RAG(BM25+벡터 검색이 아님)
