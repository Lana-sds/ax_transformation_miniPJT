# 학습 노트 참조 링크 전수 조사와 허용 목록 후보

상태: 반영함(2026-11-05, 사용자 승인 "전부 반영"). 3절 후보 28행 중 27행을 [page-allowlist.md](../../02-spec-design/output/page-allowlist.md)에 더했다. 원문 확인으로 정한 상태는 그 파일에 있다. https://reference.langchain.com/python/langgraph/graph/message 는 `get_symbol`이 다른 심볼(`LangGraphDeprecationWarning.message`)을 돌려줘 뺐다. 아래 표의 "미확인"은 조사 당시 상태다.
조사 날짜: 2026-11-05
조사 대상: 학습 노트 저장소 `sds-ax-practice` 커밋 `20df7f6`(2026-11-03, GR-8.3)의 `day*_practice/docs/**/*.md`. 파일 35개(day2 3, day3 9, day4 7, day5 7, day6 4, day7 5). day1에는 `docs/`가 없다.
조사 수단:
- 링크 추출: 정규식으로 `http(s)://` URL을 뽑았다. 앵커(`#...`)와 끝의 `/`, `.md`를 떼고 같은 페이지끼리 묶었다.
- 허용 목록 대조: `packs/langchain/allowlist.yaml`의 `path`와 같은지 봤다.
- 존재 확인: 문서는 `docs-langchain` MCP에서 `.mdx` 파일(없으면 `index.mdx`)이 있는지와 첫 제목을 봤다. API 레퍼런스는 `reference-langchain` MCP `get_symbol` 출력 첫 줄이 `# <symbol>`인지 봤다.

## 1. 요약

| 구분 | 고유 링크 수 |
| --- | --- |
| 전체 | 89 |
| LangChain 문서(`docs.langchain.com`) | 41 |
| LangChain API 레퍼런스(`reference.langchain.com`) | 12 |
| 그 밖(GR-1.1 밖) | 36 |
| 이미 허용 목록에 있음 | 18 (+ 경로 표기만 다른 1) |
| 추가 후보(존재 확인됨) | 26 (+ JavaScript 링크 대신 넣은 Python판 1) |
| 보류 | 4 |
| 제외(LangChain 링크지만 쓸 수 없음) | 4 |

- day2(RAG) 노트에는 링크가 하나도 없다.
- "상태" 열의 `확인`·`근접`은 원문에서 주제 내용을 읽어야 정한다(page-allowlist.md "읽는 법"). 이번 조사는 존재와 제목만 봤으므로 후보의 상태는 모두 **미확인**이다.

## 2. 이미 허용 목록에 있는 링크

| 경로 | 노트 일차 | 허용 목록 주제 |
| --- | --- | --- |
| `/oss/python/langchain/agents` | day3 | LangGraph 기초 #5 ReAct |
| `/langsmith/studio` | day3 | LangGraph 기초 #6 LangSmith Studio |
| `/oss/python/langgraph/workflows-agents` | day3 | Tool·MCP #2 ToolNode, 운영 품질 #1 Plan-and-Execute |
| `/oss/python/langchain/tools` | day3, day4 | Tool·MCP #1 `@tool` |
| https://reference.langchain.com/python/langgraph.prebuilt/tool_node/ToolNode | day3, day4 | Tool·MCP #2 ToolNode |
| `/oss/python/langchain/mcp/tools` | day4 | Tool·MCP #6 장애 주입 |
| `/oss/python/langchain/middleware/overview` | day5 | 미들웨어 #1 훅 호출 순서 |
| `/oss/python/langgraph/interrupts` | day5 | 미들웨어 #4 `interrupt()` |
| `/oss/python/langgraph/persistence` | day5, day7 | 미들웨어 #3, 운영 품질 #2 |
| `/oss/python/langchain/guardrails` | day5 | 미들웨어 #5 가드레일 |
| `/oss/python/langchain/multi-agent/handoffs` | day6 | 멀티 에이전트 #2 handoff |
| `/oss/python/langchain/multi-agent/subagents` | day6 | 멀티 에이전트 #1, #4 |
| `/oss/python/langgraph/use-subgraphs` | day6 | 멀티 에이전트 #3 계층 구조 |
| `/oss/python/migrate/langgraph-supervisor` | day6 | 멀티 에이전트 #1 Supervisor |
| `/oss/python/deepagents/overview` | day7 | 운영 품질 #1 Plan-and-Execute |
| `/oss/python/langchain/short-term-memory` | day7 | 운영 품질 #2, 미들웨어 #3 |
| `/oss/python/concepts/memory` | day7 | 운영 품질 #2 |
| `/langsmith/llm-as-judge` | day7 | 운영 품질 #4 LLM-as-judge |
| `/oss/python/langchain/multi-agent` | day6 | 경로 표기만 다르다. 파일은 `multi-agent/index.mdx`이고 허용 목록에 `/oss/python/langchain/multi-agent/index`로 있다 |

## 3. 추가 후보

"주제"는 노트 파일 내용과 페이지 제목으로 붙인 제안이다. 상태는 모두 미확인이다.

### LangGraph 기초 (day3)

| # | 주제 | 경로 | 종류 | 페이지 제목 | 노트 출처 |
| --- | --- | --- | --- | --- | --- |
| 1 | State·노드·엣지 | https://reference.langchain.com/python/langgraph/graph/state/StateGraph | api-ref | `StateGraph` | `day3_practice/docs/03_state_schema_typeddict.md:3`, `:282`, `05_stategraph_methods.md:3` |
| 1 | State·노드·엣지 | https://reference.langchain.com/python/langgraph/graph/state/CompiledStateGraph | api-ref | `CompiledStateGraph` | `day3_practice/docs/03_state_schema_typeddict.md:3` |
| 4 | `add_messages` 리듀서 | https://reference.langchain.com/python/langgraph/graph/message/add_messages | api-ref | `add_messages` | `day3_practice/docs/04_messages_annotated_add_messages.md:3` |
| 4 | `add_messages` 리듀서 | https://reference.langchain.com/python/langgraph/graph/message | api-ref | `message`(모듈) | `day3_practice/docs/04_messages_annotated_add_messages.md:3` |
| 4 | `add_messages` 리듀서 | `/oss/python/langchain/messages` | docs | Messages | `day3_practice/docs/07_messages_and_toolnode.md:3` |
| 5 | ReAct | https://reference.langchain.com/python/langchain/agents/factory/create_agent | api-ref | `create_agent` | `day3_practice/docs/06_react_to_langgraph.md:3` |
| 6 | LangSmith Studio | `/langsmith/application-structure` | docs | Application structure | `day3_practice/docs/09_langsmith_studio.md:3` |

### 미들웨어 · HITL · 가드레일 (day5)

| # | 주제 | 경로 | 종류 | 페이지 제목 | 노트 출처 |
| --- | --- | --- | --- | --- | --- |
| 3 | checkpointer·`thread_id` | `/oss/python/langgraph/checkpointers` | docs | Checkpointers | `day5_practice/docs/03_checkpointer_thread_id.md:3` |
| 3 | checkpointer·`thread_id` | `/oss/python/langgraph/use-time-travel` | docs | Use time-travel | `day5_practice/docs/03_checkpointer_thread_id.md:314` |
| 4 | `interrupt()`·`Command(resume)` | https://reference.langchain.com/python/langgraph/types/Command | api-ref | `Command` | `day5_practice/docs/04_interrupt_command.md:3` |
| 4 | `interrupt()`·`Command(resume)` | https://reference.langchain.com/python/langgraph/types/Interrupt | api-ref | `Interrupt` | `day5_practice/docs/04_interrupt_command.md:3` |
| 4 | `interrupt()`·`Command(resume)` | `/oss/python/deepagents/human-in-the-loop` | docs | Human-in-the-loop | `day5_practice/docs/02_hitl_interrupt_checkpointer.md:3` |

### 멀티 에이전트 (day6)

| # | 주제 | 경로 | 종류 | 페이지 제목 | 노트 출처 |
| --- | --- | --- | --- | --- | --- |
| 4 | 서브 Agent 설계 | `/oss/python/deepagents/subagents` | docs | Subagents | `day6_practice/docs/00_multi_agent_overview.md:3`, `01_multi_agent_abstraction_stack.md:3` |
| 4 | 서브 Agent 설계 | `/oss/python/deepagents/dynamic-subagents` | docs | Dynamic subagents | `day6_practice/docs/01_multi_agent_abstraction_stack.md:3` |

### 운영 품질 (day7)

| # | 주제 | 경로 | 종류 | 페이지 제목 | 노트 출처 |
| --- | --- | --- | --- | --- | --- |
| 1 | Plan-and-Execute | https://reference.langchain.com/python/langchain/agents/middleware/todo | api-ref | `todo`(모듈) | `day7_practice/docs/03_plan_execute_state_to_deep_agents.md:3` |
| 1 | Plan-and-Execute | https://reference.langchain.com/python/langchain/agents/middleware/todo/PlanningState | api-ref | `PlanningState` | `day7_practice/docs/03_plan_execute_state_to_deep_agents.md:3` |
| 2 | 단기·장기 기억 | `/oss/python/langgraph/checkpointers` | docs | Checkpointers | `day7_practice/docs/02_agent_memory_context_layers.md:6` |
| 2 | 단기·장기 기억 | `/oss/python/langgraph/stores` | docs | Stores | `day7_practice/docs/02_agent_memory_context_layers.md:6` |
| 2 | 단기·장기 기억 | `/oss/python/deepagents/memory` | docs | Memory | `day7_practice/docs/02_agent_memory_context_layers.md:6` |
| 2 | 단기·장기 기억 | `/oss/python/concepts/context` | docs | Context overview | `day7_practice/docs/02_agent_memory_context_layers.md:6` |
| 2 | 단기·장기 기억 | `/oss/python/deepagents/context-engineering` | docs | Context engineering in Deep Agents | `day7_practice/docs/02_agent_memory_context_layers.md:6` |
| 2 | 단기·장기 기억 | `/oss/python/langchain/context-engineering` | docs | (노트 링크는 JavaScript판. Python판이 있어 대신 넣는다) | `day7_practice/docs/02_agent_memory_context_layers.md:6` |
| 3 | 콜백 관측 | `/oss/python/langchain/models` | docs | Models(노트 앵커 `#callback-handler`) | `day7_practice/docs/05_callback_vs_middleware.md:3` |
| 3 | 콜백 관측 | https://reference.langchain.com/python/langchain-core/callbacks | api-ref | `callbacks`(모듈). 허용 목록에는 `callbacks/base/BaseCallbackHandler`가 있다 | `day7_practice/docs/05_callback_vs_middleware.md:3` |
| 4 | LLM-as-judge | `/langsmith/llm-as-judge-sdk` | docs | How to define an LLM-as-a-judge evaluator | `day7_practice/docs/04_llm_as_judge_evaluation.md:3` |
| 4 | LLM-as-judge | `/langsmith/trajectory-evals` | docs | How to evaluate your agent with trajectory evaluations(노트 앵커 `#llm-as-judge-evaluator`) | `day7_practice/docs/04_llm_as_judge_evaluation.md:3` |
| 4 | LLM-as-judge | `/langsmith/create-few-shot-evaluators` | docs | How to improve your evaluator with few-shot examples | `day7_practice/docs/04_llm_as_judge_evaluation.md:3` |
| 4 | LLM-as-judge | `/langsmith/improve-judge-evaluator-feedback` | docs | Improve LLM-as-judge evaluators using human feedback | `day7_practice/docs/04_llm_as_judge_evaluation.md:3` |

- `/oss/python/langgraph/checkpointers`는 미들웨어 #3과 운영 품질 #2 두 곳에 후보로 올렸다. 고유 페이지로는 27개, 행으로는 28개다.
- `todo`, `PlanningState`를 넣어도 "Plan-and-Execute"라는 이름이 문서에 없으면 그 주제는 `근접`으로 남는다.

## 4. 보류

LangChain 공식 페이지이고 존재도 확인했지만 34개 주제에 바로 붙지 않는다.

| 경로 | 페이지 제목 | 노트 출처 | 보류 이유 |
| --- | --- | --- | --- |
| `/oss/python/langgraph/overview` | LangGraph overview | `day3_practice/docs/01_langgraph_overview.md:3` | 개요 페이지. 특정 주제의 근거로 쓰기 어렵다 |
| `/oss/python/concepts/products` | Runtimes, frameworks, and harnesses | `day7_practice/docs/01_react_vs_plan_and_execute.md:3`, `02_agent_memory_context_layers.md:6` | 제품 구분 개요. 주제 매핑이 없다 |
| `/langsmith/double-texting` | Double texting | `day5_practice/docs/02_hitl_interrupt_checkpointer.md:3` | LangSmith 배포 서버의 동시 실행 처리. HITL 주제와 직접 맞지 않는다 |
| `/oss/deepagents/code/mcp-tools` | MCP tools | `day4_practice/docs/06_langchain_mcp_adapters.md:7` | Deep Agents Code(코딩 에이전트 제품)의 `.mcp.json` 설정 문서. Python 라이브러리 문서가 아니다 |

## 5. 제외

### LangChain 링크지만 쓸 수 없음

| 링크 | 노트 출처 | 이유 |
| --- | --- | --- |
| `/oss/javascript/langgraph/workflows-agents` | `day4_practice/docs/02_toolnode.md:3` | JavaScript 문서. Python판 `/oss/python/langgraph/workflows-agents`는 이미 있다 |
| `/oss/javascript/langchain/context-engineering` | `day7_practice/docs/02_agent_memory_context_layers.md:6` | JavaScript 문서. Python판을 3절 후보로 넣었다 |
| https://reference.langchain.com/python/langchain-mcp-adapters | `day4_practice/docs/06_langchain_mcp_adapters.md:3` | 패키지 첫 페이지라 `fetch-ref`(심볼 단위)로 받을 수 없다. 심볼 행 2개는 이미 있다 |
| `https://docs.langchain.com/mcp` | `day4_practice/docs/06_langchain_mcp_adapters.md:430` | 문서 페이지가 아니다. 설정 예시 안의 docs MCP 서버 URL이다 |

### GR-1.1 밖 출처

GR-1.1은 LangChain·LangGraph 공식 문서와 API 레퍼런스만 근거로 인정한다. 아래는 허용 목록에 넣을 수 없다.

| 출처 | 고유 링크 수 | 노트 일차 | 비고 |
| --- | --- | --- | --- |
| `code.claude.com` | 12 | day5, day6 | Claude Code 문서. CCA-F 팩에서 쓸 수 있다 |
| `modelcontextprotocol.io` | 5 | day4 | MCP 명세 |
| `gofastmcp.com` | 3 | day4 | FastMCP 문서. Tool·MCP #3 "FastMCP 서버"는 여전히 `없음`이다 |
| `arxiv.org` | 5 | day7 | ReAct, Plan-and-Solve 등 논문 |
| `github.com` | 5 | day4, day7 | 저장소, 릴리스, 소스 파일 |
| `docs.smith.langchain.com` | 1 | day3 | 옛 LangSmith 도메인 첫 페이지 |
| `langfuse.com` | 1 | day3 | Langfuse 문서 |
| `openai.github.io` | 1 | day6 | OpenAI Agents SDK 문서 |
| 예시·로컬 주소 | 3 | day3, day4 | `example.com/mcp`, `localhost:8000/mcp`, `127.0.0.1:2024` |

## 6. 반영하려면

1. 이 문서의 3절에서 넣을 행을 고른다(사용자 승인).
2. 고른 행의 원문을 열어 상태(`확인`·`근접`)와 확인 근거를 적어 `page-allowlist.md`에 더한다.
3. `quiz snapshot fetch <page...>`, `quiz snapshot fetch-ref <url...>`로 스냅샷을 받는다.
4. `quiz allowlist build`로 `allowlist.yaml`을 다시 만든다.
5. 이미 생성한 문제에는 영향이 없다. 새 행은 다음 `generate`부터 근거 페이지로 쓰인다.
