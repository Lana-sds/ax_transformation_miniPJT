# 1 미결 사항 닫기 기록

상태: 완료
시작: 2026-11-04 14:41
완료: 2026-11-04 14:47
계획: [02-spec-design-plan.md](../02-spec-design-plan.md)의 1단계

## 0단계 사전 준비 (2026-11-04 14:41)

- ouroboros MCP: 응답함. `ouroboros_session_status(interview_20261104_041911)`는 여전히 "No events found for session"
- `reference-langchain` MCP: 응답함(`search_api` "ChatBedrockConverse")
- `docs-langchain` MCP: 응답함(`ls /oss/python/langchain`)
- `docs/02-spec-design/input/README.md`에 입력 링크 4개를 적었다

## 입력

- `requirements.md` 6장 11개 항목
- 지시: `/stage 2 run`

## 진행

### `readchk`

- 호출 방식: 메인 세션이 Skill 도구로 직접 호출했다.
- 이해한 내용: 계획 1단계만 수행한다. 미결 11개 중 6개는 결정을 받고, 4개는 기본값을 받아 3단계로 넘기고, 허용 목록은 2단계로 둔다. 결과는 `design.md`를 초안으로 만들어 결정 장에만 적는다.
- 맥락으로 풀린 것: `design.md`를 1단계에서 미리 만드는 것(계획 1단계 끝나는 조건에 명시). 분류(계획 결정 3).
- 질문으로 올린 갈림길: 없음

### 질문과 답

메인 세션이 항목마다 기본안(Recommended)과 대안 하나를 냈다. 질문 2묶음, 8개.

| 번호 | 항목 | 기본안 | 대안 | 답 |
| --- | --- | --- | --- | --- |
| 1 | "통과" 정의 | 게이트 3개 + Judge, 감사는 표본만 | 감사까지 포함 | 기본안 |
| 2 | 인용 정규화 | NFKC + 공백 축약만, 30자 이상 | 인라인 마크다운도 제거 | 기본안 |
| 3 | 단답 범위 | 식별자·단일 용어, 허용 답안 최대 5개 | 3단어 이하 구절 허용 | 기본안 |
| 4 | 유사 중복 | 같은 quote 또는 Jaccard ≥ 0.6 (결정적) | Judge 판단 | 기본안 |
| 5 | 감사 시드 | 스냅샷 ID에서 파생 | 고정 정수 시드 | 기본안 |
| 6 | 첫 세트 | 빈 자리는 새 문제로, 항상 10개 | 새 문제 7개 고정 | 기본안 |
| 7 | CORS | Vite 프록시 | `CORSMiddleware` | 기본안 |
| 8 | 운영 기본값 3개(Bedrock, SQLite, 생성 시간) | 모두 채택 | 배치 비용 상한 추가 | 기본안 |

## 결정

결정 원본은 [design.md](../../02-spec-design/output/design.md) 1장이다.

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 닫음 6개 | 통과 정의, 인용 정규화, 감사 시드, 단답 범위, 첫 세트, 유사 중복 | 없음. 단답 채점 정규화에 백틱·끝 `()` 제거를 더했다(FR-3 확장) |
| 3단계로 넘김 4개 | Bedrock 운영, CORS, SQLite 운영, 생성 시간. 기본값 있음 | 없음. 비용 상한은 요구사항대로 두지 않았다 |
| 2단계에서 다룸 1개 | 페이지 허용 목록 | 없음 |

## 계획과 다른 점

- 사용자 지적(완료 확인 직전): 입력 README에 `bedrock-model-list.md`, `design-option-a-docs-mcp-grounding.md`, `tech-stack-common.md`가 빠져 있었다. `requirements.md`가 입력 문서로 적은 파일이다. README와 계획 입력 목록에 추가하고 계획 상단에 "수정:" 줄을 남겼다. 1단계 결정에는 영향이 없다

## 끝나는 조건 확인

- 조건: 11개 모두 "닫힘", "3단계로 넘김(기본값 있음)", "2단계에서 다룸" 중 하나. 결정이 `design.md` 결정 장 초안에 있음
- 결과: 충족. 닫힘 6, 넘김 4, 2단계 1. `design.md` 1장 초안에 반영
