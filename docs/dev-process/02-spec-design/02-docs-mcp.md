# 2 docs MCP 허용 목록 기록

상태: 완료
시작: 2026-11-04 14:47
완료: 2026-11-04 14:55
계획: [02-spec-design-plan.md](../02-spec-design-plan.md)의 2단계

## 입력

- `requirements.md` 1.4 표의 주제 34개(버킷 6개: RAG 7, LangGraph 기초 6, Tool·MCP 6, 미들웨어·HITL·가드레일 5, 멀티 에이전트 5, 운영 품질 5)
- 지시: "응, 2단계 진행해"

## 진행

- 버킷 6개를 서브에이전트 6개(모델 sonnet)에 나눠 맡겼다(계획 2단계 허용 사항). 각 서브에이전트는 `docs-langchain`, `reference-langchain` MCP만 쓴다. 규칙: Python 문서만, 검색 결과만으로는 확인으로 치지 않고 `.mdx`를 열어 확인, 주제당 1~3개.
- 서브에이전트 사용량: 약 9.9만~11.2만 토큰씩, 도구 호출 5~15회, 29~66초.

### 메인 세션 재확인

계획 조건(버킷마다 2개 이상 다시 열기)에 따라 직접 열었다.

| 버킷 | 다시 연 경로 | 결과 |
| --- | --- | --- |
| RAG | `knowledge-base`, `integrations/splitters`, `integrations/embeddings` | 확인. 서브에이전트가 "하이브리드 검색 문서 없음"으로 보고했으나 `embeddings` 159행 "Sparse and hybrid retrieval"을 찾아 문서 행을 더했다 |
| LangGraph 기초 | `/oss/python/langgraph/studio`, `/oss/python/langchain/agents` | studio는 서브에이전트가 열지 않은 경로였다. 열어서 확인. agents에 "ReAct" 표현 없음(근접) |
| Tool · MCP | `workflows-agents` 1111행 "### ToolNode", `migrate/langchain-mcp-adapters`, `MCPAdapter` 레퍼런스 | 확인. `@tool` 레퍼런스 URL은 `search_api`로 나오지 않아 뺐다 |
| 미들웨어 · HITL · 가드레일 | `middleware/custom`, `interrupts`, `guardrails` | 확인 |
| 멀티 에이전트 | `handoffs-customer-support`, `migrate/langgraph-supervisor`, `rg -il hierarch` | 확인. handoffs-customer-support는 서브에이전트가 `ls`로만 본 경로였다. 계층 구조 관련 멀티 에이전트 문서 없음 |
| 운영 품질 | `test/evals`, `workflows-agents` 550행, `BaseCallbackHandler` 레퍼런스 | evals는 서브에이전트가 열지 않은 경로였다. 열어서 확인. 콜백 레퍼런스 행을 더했다 |

### 서브에이전트 보고를 고친 곳

- 추가 3개: 하이브리드 검색 문서 행, 콜백 `BaseCallbackHandler` 레퍼런스, LLM-as-judge의 `test/evals` 행
- 확인으로 올림 3개: `/oss/python/langgraph/studio`, `handoffs-customer-support`, `test/evals`(서브에이전트가 열지 않은 경로)
- 뺀 것 5개: `create_react_agent`(deprecated), `create_supervisor` 레퍼런스(패키지 관리 중단), `@tool` 레퍼런스(확인 안 됨), `cohere-reranker`(파일 없음), `CohereRerank` 레퍼런스(타사 API 전용, 재랭킹은 `ContextualCompressionRetriever`로 충분)

### 발견: 문서 최신 버전과 고정 버전의 충돌

- 현재 문서는 MCP를 `langchain.mcp`의 `MCPAdapter`(FastMCP 기반)로 설명한다. `migrate/langchain-mcp-adapters`는 "`MultiServerMCPClient` is collapsed into a single `MCPAdapter` class"라고 적는다.
- requirements GR-7은 샌드박스에 `langchain-mcp-adapters==0.3.2`, `fastmcp==2.13.0`을 고정했다. 교안 코드는 `MultiServerMCPClient`를 쓴다(1단계 기록).
- `MultiServerMCPClient` 레퍼런스가 어느 패키지 버전 기준인지, 고정한 `fastmcp==2.13.0`이 `langchain.mcp`와 맞는지는 미확인이다.
- 같은 문제가 덜한 형태로 두 곳에 더 있다: `create_react_agent` deprecated, `langgraph-supervisor` 관리 중단.

### 질문과 답

- 질문: MCP 문제의 기준을 현재 문서(`MCPAdapter`, GR-7 고정 해제), 고정 버전(0.3.2 API), MCP 코드형 출제 안 함 중 무엇으로 할까. 메인 세션 추천은 현재 문서 기준이었다.
- 답: MCP 코드형 출제 안 함

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| MCP 문제 범위 | MCP 주제는 현재 문서 기준 개념·설계 문제만. 코드형은 내지 않는다. Tool·MCP 코드형은 `@tool`, ToolNode, 재시도·장애 처리에서만 | 없음. GR-7 고정 버전은 그대로 둔다. 코드형에서 MCP 고정 버전을 쓸 일이 거의 없어진다 |
| FastMCP 서버 주제 | 출제하지 않는다. 허용 목록에 페이지가 없다 | requirements 1.4 주제 34개 중 1개가 빠진다 |
| 근접 행 | ReAct, 계층 구조, Plan-and-Execute는 가장 가까운 문서만 있다. 문서가 그 이름으로 패턴을 정의한다고 쓰지 않는다 | 없음 |

## 계획과 다른 점

- 계획에 없던 사용자 질문 1개(MCP 버전 충돌). 끝나는 조건과 도구는 바뀌지 않았다.

## 끝나는 조건 확인

- 조건: 모든 주제가 페이지 1개 이상 또는 "페이지 없음(이유)" 상태. 모든 경로를 실제 조회로 확인했고 조회 날짜가 있음. `output/page-allowlist.md` 초안이 있음
- 결과: 충족. 34개 주제 중 확인 30, 근접만 3, 없음 1(FastMCP 서버, 이유 기재). 모든 행 조회 날짜 2026-11-04. 서브에이전트가 열지 않은 경로 3개는 메인 세션이 열어 확인했다
