# 02 스펙과 설계 회고

작성일: 2026-11-04
계획: [02-spec-design-plan.md](../02-spec-design-plan.md)
기록: [01-open-items.md](01-open-items.md), [02-docs-mcp.md](02-docs-mcp.md), [03-seed.md](03-seed.md), [04-design-modelchk.md](04-design-modelchk.md)
산출물: [page-allowlist.md](../../02-spec-design/output/page-allowlist.md)(확정), [seed.yaml](../../02-spec-design/output/seed.yaml)(확정 v1.0.1), [design.md](../../02-spec-design/output/design.md)(확정)

## 도구별 평가

| 도구 | 새로 드러낸 결정 수 | 다른 도구와 겹친 질문 수 | 바꾼 기존 결정 수 | 걸린 시간 | 다음 프로젝트에서도 쓸 것인가 |
| --- | --- | --- | --- | --- | --- |
| 도구 없음(메인 세션, 1단계 미결 사항) | 0 | 0 | 0 | 6분(0단계 포함) | 해당 없음. 질문 8개로 11개를 분류했다 |
| `docs-langchain`, `reference-langchain` MCP | 3 | 0 | 1 | 8분 | 예. GR-3의 "실제 조회" 근거를 만든 유일한 수단이다. 서브에이전트 결과는 다시 확인해야 한다 |
| ouroboros `seed`(`generate_seed`, `qa`) | 7 | 0 | 0 | 9분 | 예, 조건부. `session_context` 경로는 빠르다. 온톨로지가 비어 나오므로 직접 채운다고 보고 쓴다 |
| paperthin `modelchk` | 0 | 0 | 0 | 미확인(4단계 안, 15:12 한 번) | 예. 비용이 낮다. 권고가 맞았는지는 3단계 회고에서 확인한다 |
| paperthin `readchk` | 0 | 0 | 0 | 미확인(1단계, 4단계 시작 때 각 1회) | 예. 비용이 낮다. 이번 단계에서는 갈림길을 하나도 올리지 않았다 |

- 새로 드러낸 결정: 입력 문서의 열린 질문(requirements 6장 11개)에 없던 결정이다.
  - docs MCP 3개: MCP 문제 범위(코드형 제외), FastMCP 서버 주제 출제 안 함, 근접 행 표현 규칙. [02-docs-mcp.md](02-docs-mcp.md) "결정"
  - `seed` 7개: QA 1·2차 지적에서 나온 구현 값 빈칸. `design.md` 1.3 원래 목록의 항목 수다. 타임아웃(Bedrock·샌드박스), 배치 재개·멱등, 소진 뒤 채우는 순서, 지표 파일 경로·단가표, Langfuse 연결, 면제 기록, `mistake_tag` 빈 값. Seed 제약으로 `design.md`에 넘겼고 4단계에서 닫았다. [03-seed.md](03-seed.md) "QA 자문", [design.md](../../02-spec-design/output/design.md) 1.3
- 바꾼 기존 결정: docs MCP 1개. requirements 1.4의 주제 34개 중 FastMCP 서버가 빠졌다.
- 수치 근거: 걸린 시간은 각 기록의 시작·완료 시각이다. 01 14:41~14:47, 02 14:47~14:55, 03 14:55~15:04, 04 15:05~15:17. 04의 12분에는 사용자가 다른 세션에서 `design.md`를 검토·추가한 시간이 들어 있다. 단계 전체는 14:41~15:17, 36분이다.

### 계획 5장의 추가 기준

| 기준 | 값 | 근거 |
| --- | --- | --- |
| 미결 사항 11개 | 닫음 6, 3단계로 넘김(기본값 있음) 4, 2단계에서 다룸 1 | [01-open-items.md](01-open-items.md) "결정" |
| 허용 목록 | 주제 34개 중 페이지 확보 33(확인 30, 근접만 3), API 레퍼런스로만 확보 0, 페이지 없음 1(FastMCP 서버). 표 74행 | [page-allowlist.md](../../02-spec-design/output/page-allowlist.md) "요약" |
| Seed | QA 0.50 → 0.72(둘 다 REVISE, 기준 0.90). 빈칸 질문 0개. 직접 편집 6구분(온톨로지, 수용 기준 12→9, 측정 가능화, 모순 해소, 표현 정리, 받지 않은 지적) | [03-seed.md](03-seed.md) |
| `modelchk` 권고와 3단계 실제 등급 | 미확인. 3단계 회고에서 확인 | [04-design-modelchk.md](04-design-modelchk.md) "`modelchk`" |

### 도구별 메모

- docs MCP: 서브에이전트 6개(sonnet, 약 9.9만~11.2만 토큰씩, 29~66초)가 버킷을 나눠 맡았다. 메인 세션 재확인에서 고친 곳이 11개다. 추가 3, 확인으로 올림 3, 뺀 것 5. 서브에이전트가 "없음"으로 보고한 하이브리드 검색 문서를 메인 세션이 찾았다. 서브에이전트 보고만으로는 허용 목록을 확정할 수 없다.
- docs MCP: 문서 최신 버전(`MCPAdapter`)과 GR-7 고정 버전(`MultiServerMCPClient`)의 충돌을 드러냈다. 계획에 없던 사용자 질문 1개가 여기서 나왔다.
- `seed`: `session_context`로 넘긴 값은 그대로 들어갔다. 그러나 `ontology_schema.fields`가 빈 목록, `evaluation_principles`와 `exit_conditions`가 일반 문구 1개씩이었다. QA 1차가 이를 짚었다. 도구는 Seed를 파일로 저장하지 않았다. `output/seed.yaml`이 유일한 사본이다.
- `seed` QA: 2차 지적 6개(기준 겹침, 과정 섞임, 면제-기준 충돌, 미룬 값, 모호한 제약, 온톨로지 개체 누락)는 고치지 않고 남겼다. 이 중 미룬 값과 `mistake_tag` 조건은 `design.md` 1.3에서 닫혔다.
- `modelchk`: 14개 단위 중 frontier는 W6 하나다. thorough 5개, measured 6개, glance 2개. 앱의 Bedrock 모델과 섞지 않았다.
- `readchk`: 두 번 모두 맥락으로 풀려 질문 없이 진행했다. 다만 사용자가 지적한 두 빈칸(입력 README 누락, 설계 문서의 아키텍처·기술 스택 누락)은 잡지 못했다. 둘 다 "계획을 맞게 읽었나"가 아니라 "계획 자체가 빠뜨렸나"의 문제라 `readchk`의 범위 밖이다.

## 계획 대비

- 입력 누락: 0단계 입력 README에 `bedrock-model-list.md`, `design-option-a-docs-mcp-grounding.md`, `tech-stack-common.md`가 빠졌다. 원인은 계획 1장 입력 목록이 `requirements.md`의 "입력 문서" 줄을 옮기지 않은 것이다. 사용자 지적으로 고쳤다.
- 계획에 없던 질문: MCP 버전 충돌(2단계). 끝나는 조건과 도구는 바뀌지 않았다.
- QA 횟수: 계획은 1회였다. 사용자가 개선 패스 대신 직접 편집을 골랐고, 편집 확인용으로 1회 더 돌렸다(총 2회).
- `design.md` 구성: 계획 4단계 구성 목록에 아키텍처 개요와 기술 스택·실행 환경이 없었다. 사용자가 다른 세션에서 2.1·2.2를 추가했고 계획에 "수정:" 줄이 남았다. 원인은 계획이 "요구사항 FR별 설계"만 나열하고 설계 문서의 기본 장을 점검하지 않은 것이다.
- `modelchk` 호출 방식: 계획은 "작업 단위마다 `modelchk`를 불러"였다. 실제로는 14개 단위를 한 번에 넘겨 한 번 호출했다. 권고는 단위별로 받았다. 기록 파일에 적지 않은 차이라 여기 남긴다.
- 사용자 재검토에서 고친 곳 2개: `design.md` 2.3의 근거 표기 `(1.3)`과 2.2의 `AWS_REGION` 처리. [04-design-modelchk.md](04-design-modelchk.md) "끝나는 조건 확인"
- 시간 상자(계획 결정 6): 2026-11-04 안에 끝났다. 시작·완료 시각을 기록해 1단계 회고의 "측정하지 못함"을 해소했다.

## lifecycle 문서 수정안

[skillset-by-lifecycle.md](../skillset-by-lifecycle.md)는 직접 고치지 않았다. 사용자가 반영 여부를 정한다.

1. "이 프로젝트의 선택" 절에 한 줄 추가: "1단계에서 ouroboros `interview`를 썼으면 2단계는 ouroboros `seed`로 이어 간다. superpowers는 3단계(구현)부터 쓴다." 현재 절은 "기본 superpowers 하나"와 "계획 도구는 하나만"만 있다. 이번 단계는 1단계 인터뷰와 5단계 `evaluate`를 잇기 위해 ouroboros를 골랐다.
2. "2. 스펙과 설계" 행 이유 열에 한 줄 추가: "`seed`의 `session_context` 경로는 온톨로지를 비워 둔다. 생성 직후 QA를 한 번 돌리고 온톨로지는 직접 채운다."
3. "이 프로젝트의 선택" 절에 한 줄 추가: "근거를 공식 문서로 제한하는 프로젝트는 2단계에서 `docs-langchain`, `reference-langchain` MCP로 페이지 허용 목록을 만든다. 서브에이전트로 나누면 메인 세션이 버킷마다 다시 연다." lifecycle 표의 도구 범주(gstack, superpowers 등)에 없는 MCP라 행이 아니라 프로젝트 절에 둔다.

## 다음 단계로 넘길 것

- `page-allowlist.md`: 사용자가 확정했다(2026-11-04). 3단계 W2의 입력이다.
- 3단계 입력: `seed.yaml`(수용 기준 9개), `design.md`(작업 단위 W1~W14, 의존, `modelchk` 권고), `page-allowlist.md`
- 미확인 사항(`design.md`에 적힘):
  - 앱 Python과 langchain·langgraph 버전(교안 기준, W1)
  - 스냅샷 수집 방법, MCP 서버 URL, 30KB 출력 한도 처리(W2 첫 작업)
  - Langfuse SDK의 세션·태그 키 이름(W4)
  - Bedrock 단가(W4)
  - botocore의 `AWS_REGION` 인식. `region_name`으로 직접 넘겨 회피했다
- Seed QA 2차의 남은 지적 6개: 3단계에서 Seed를 고칠지, 5단계 `evaluate` 전에 고칠지 정한다.
- 3단계 도구: lifecycle 1순위 superpowers는 이 환경에 설치되어 있지 않다(2026-11-04 확인). 설치 여부와 Seed·`design.md`와의 트리거 충돌은 3단계 계획에서 다룬다.
- 3단계 회고에서 확인: `modelchk` 권고와 실제 사용 등급의 일치 여부
- 커밋 전 상태: 2단계 산출물과 기록, 사용자가 고친 `bedrock-model-list.md`가 커밋되지 않았다(브랜치 `Lana-sds/02-spec-design`).
