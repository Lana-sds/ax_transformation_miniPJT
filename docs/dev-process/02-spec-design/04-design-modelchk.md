# 4 설계 문서와 `modelchk` 기록

상태: 완료
시작: 2026-11-04 15:05
완료: 2026-11-04 15:17
계획: [02-spec-design-plan.md](../02-spec-design-plan.md)의 4단계

## 입력

- [seed.yaml](../../02-spec-design/output/seed.yaml) v1.0.1(수용 기준 9개, 제약 20개, 온톨로지 개체 11개)
- [requirements.md](../../01-requirements/output/requirements.md), [design.md](../../02-spec-design/output/design.md) 1장(1단계 결정), [page-allowlist.md](../../02-spec-design/output/page-allowlist.md)
- [bedrock-model-list.md](../../01-requirements/input/bedrock-model-list.md), [design-option-a-docs-mcp-grounding.md](../../01-requirements/input/design-option-a-docs-mcp-grounding.md), [tech-stack-common.md](../../01-requirements/input/tech-stack-common.md)
- 지시: `/stage 2 run`(1~3단계 기록이 "완료"라 4단계부터 시작)

## 진행

### `readchk` (15:06)

- 호출 방식: 메인 세션이 Skill 도구로 직접 호출했다.
- 이해한 내용(understood as): `design.md`에 1.3절(Seed가 넘긴 구현 값 7개)의 결정을 채우고, 2장 이후로 코드 배치, 모듈 책임, DB 테이블, HTTP·CLI 접점, 문제 1개를 처리하는 그래프, 3단계 구현 단위 목록을 쓴다. 단위마다 수용 기준 번호와 코딩 에이전트용 등급·강도를 붙인다. 앱의 Bedrock 모델은 손대지 않는다.
- 맥락으로 풀린 것: 1.3절 값을 사용자에게 하나씩 묻지 않고 초안으로 정한 뒤 끝나는 조건의 "사용자 검토"에서 확인받는다(계획 4단계 "메인 세션이 `design.md`를 쓴다").
- 질문으로 올린 갈림길: 없음

### 확인한 사실

- `ChatBedrockConverse`에 `config` 필드가 있고 응답에 `usage_metadata`(입력·출력 토큰)가 있다. `reference-langchain` `get_symbol`, 2026-11-04.
- Langfuse SDK의 세션·태그 설정 키 이름: 미확인. 3단계에서 확인한다고 `design.md` 1.3에 적었다.
- Bedrock 단가: 미확인. `data/pricing/bedrock.yaml`은 3단계에서 채운다.
- 스냅샷 수집 방법(MCP 서버 URL, 30KB 출력 한도): 미확인. 3단계 W2의 첫 일로 넘겼다.

### `design.md`에 쓴 장

- 1.3 구현 값 9행(타임아웃 2개, 배치 재개, 채우는 순서, 지표 파일, 단가표, Langfuse, 면제 기록, `mistake_tag` 빈 값)
- 2장 코드 디렉토리, 3장 모듈 경계, 4장 SQLite 스키마(테이블 13개), 5장 LangGraph 그래프(노드 5개, 실패 이유 코드), 6장 세트·복습·지표 규칙, 7장 API 8개와 CLI 6개, 8장 작업 단위 14개

### `modelchk` (15:12)

작업 단위 14개를 한 번에 넘겨 단위별로 받았다. 권고만이며 3단계 실행자가 실제 모델과 강도를 정한다.

| 단위 | 등급 | 강도 | 근거 | 올릴 신호 | 내릴 신호 | 검증 |
| --- | --- | --- | --- | --- | --- | --- |
| W1 골격 | fast | measured | 스키마 초안이 있고 되돌리기 쉽다. 프로젝트 3개라 단계가 여럿이다 | Windows에서 uv·Vite 설정이 막힘 | 템플릿 명령으로 끝남 | `migrate` 두 번 실행해도 같은 결과, `uv run`·`npm run dev` 기동 |
| W2 허용 목록·스냅샷 | standard | thorough | 수집 방법이 미정이고 스냅샷이 잘리면 GR-4 전체가 틀린다 | 30KB 한도로 페이지가 잘림, MCP를 코드에서 부를 수 없음 | 수집이 단순 반복으로 정리됨 | 스냅샷 sha256, 페이지별 끝부분 대조, 표 74행과 yaml 행 수 일치 |
| W3 결정적 검사 | fast | thorough | 순수 함수라 범위가 작지만 정규화 경계 사례가 까다롭다 | 마크다운·코드 블록 때문에 인용 대조 실패가 잦음 | 테스트가 처음부터 다 통과 | 단위 테스트(NFKC, 줄바꿈, 30자, Jaccard 0.6 경계, 백틱·`()`) |
| W4 Bedrock·관측 | standard | measured | 외부 SDK 두 개를 묶는 보통 작업. Langfuse 키 이름이 미확인이다 | 재시도·요청 제한 오류가 반복됨 | 문서 예제 그대로 됨 | 실제 Bedrock 1회 호출 토큰 기록, Langfuse 변수 없이 오류 없음 |
| W5 샌드박스 | standard | thorough | 프로세스 격리, Windows 타임아웃, 가짜 모델 `bind_tools` 처리가 얽힌다 | 자식 프로세스 종료·환경 변수 제거가 Windows에서 안 됨 | 예제 코드 몇 개로 바로 됨 | 무한 루프 코드 30초 종료, `AWS_*` 없는 환경 확인, lock 해시 기록 |
| W6 생성 파이프라인 | frontier | thorough | 프롬프트와 그래프 품질이 60문제 전체와 비용을 정한다. 모듈 4개를 잇는다 | 파일럿 통과율이 매우 낮음, 실패 이유가 고르게 퍼짐 | 파일럿이 첫 시도에 대부분 통과 | 파일럿 6문제의 `verification_results`, 재개 테스트, 버린 이유 기록 |
| W7 파일럿·풀 생성 | standard | thorough | 실행은 명령이지만 실패 분석과 프롬프트 조정 판단이 필요하다 | 재생성 소진이 많음, 축소 기준에 근접 | 배치가 안정적으로 통과 | 버킷·형식별 개수, 게이트 100%, 배치 비용 |
| W8 세트·채점·복습 | standard | thorough | 규칙이 많고 세트 번호 경계 사례가 있다 | 복습 간격·변형 대체에서 테스트 실패 | 규칙 테스트가 바로 통과 | `set_no` 시뮬레이션 테스트(2·5세트, 3개 상한, retired, 소진 뒤 순서) |
| W9 FastAPI | standard | measured | 일반 CRUD와 409 규칙 | 트랜잭션·동시 요청 문제 | 엔드포인트가 단순 위임 | API 테스트, 정답 키가 제출 전 응답에 없음 |
| W10 React UI | standard | measured | 화면 3개의 보통 UI 작업 | 매핑 표시·구절 선택 상호작용이 복잡해짐 | 기본 컴포넌트로 충분 | 브라우저에서 풀이·태그·감사 흐름 수동 확인 |
| W11 감사 | fast | measured | 시드·표본은 1장에 정해졌고 코드가 작다. 감사 자체는 본인 일이다 | 재감사 흐름이 꼬임 | - | 같은 스냅샷에서 같은 표본, `audit_records` 20행 |
| W12 변형 문제 | standard | measured | W6 그래프 재사용, 입력만 다르다 | 변형 통과율이 낮음 | 축소로 뺌 | `variant_of` 연결, 복습에서 변형이 나옴 |
| W13 기준선 지표 | fast | glance | SQL 집계와 JSON 쓰기 | 지표 정의가 바뀜 | - | `baseline.json` 필드가 6장과 같음 |
| W14 3세트·재시작 | fast | glance | 조회 스크립트 하나와 본인 풀이 | 조회 결과가 기준과 어긋남 | - | 재시작 뒤 SQLite 조회로 seed 수용 기준 3 확인 |

### 대응 확인

| 수용 기준 | 담당 단위 |
| --- | --- |
| 1 풀 | W2, W3, W5, W6, W7 |
| 2 감사 | W9, W10, W11 |
| 3 3세트 풀이 | W1, W9, W10, W14 |
| 4 세트 출제 | W8, W9 |
| 5 풀이 화면 | W9, W10 |
| 6 채점 | W3, W8, W9 |
| 7 복습 큐 | W8, W9, W12 |
| 8 기준선 지표 | W4, W13 |
| 9 Langfuse | W4 |

1단계 결정 반영: 통과 정의(5장 판정), 인용 정규화(W3, 5장 `gates`), 감사 시드(4장 `pool_snapshot_id`, W11), 단답 범위(5장 `gates`), 첫 세트(1.3 채우는 순서), MCP 범위(5장 슬롯 계획), 유사 중복(5장 `dedupe`), 운영 기본값 4개(1.2, 1.3, 7장).

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 1.3 구현 값 | `design.md` 1.3 표 9행 | 없음. Seed가 넘긴 빈칸을 채웠다 |
| 파이프라인 순서 | FR-7 순서(생성 → Judge → 실행 → 결정적 검사) 유지. 결정적 검사를 앞에 두는 비용 절감은 파일럿 뒤 검토 | 없음 |
| `version_conflict`, `duplicate` | 재생성 없이 버린다 | 새 규칙. FR-7 "실패 시 재생성"의 예외 |
| 복습 간격 해석 | `set_no=n`에서 틀리면 `n+2`, 1회차에서 틀리면 `m+5` | requirements "2세트 뒤", "5세트 뒤"를 세트 번호 차이로 해석 |
| 스냅샷 수집 방법 | 3단계 W2로 넘김 | 없음 |

## 계획과 다른 점

- 사용자 지적(검토 전): 설계 단계라면 아키텍처 도식과 기술 스펙 정의가 있어야 한다. 계획 4단계의 `design.md` 구성 목록에 두 항목이 없어서 빠졌다. `design.md` 2장을 2.1 아키텍처 개요(mermaid, 프로세스 표), 2.2 기술 스택·실행 환경(구성 요소, 버전·고정 방식, 근거, 환경 변수, 포트), 2.3 코드 디렉토리 구조로 나눴다. 계획 구성 목록에도 추가하고 "수정:" 줄을 남겼다
  - 로컬 도구 버전 확인(2026-11-04): Python 3.14.8, uv 0.13.7, Node v26.13.0, npm 11.20.0
  - 새로 정한 기본값: 프론트엔드 TypeScript(`react-ts`), npm 사용(Bun 미사용), pytest, 샌드박스 Python은 앱과 같은 버전, 리전 환경 변수 `AWS_REGION`
  - 미확인으로 남김: 앱 Python 버전과 langchain·langgraph 버전(교안 기준, W1에서 고정)

## 끝나는 조건 확인

- 조건: Seed의 모든 수용 기준에 담당 작업 단위가 있다. 1단계 결정이 모두 반영되었다. 사용자가 `design.md`를 검토했다
- 결과: 충족. 수용 기준 9개 모두 담당 단위가 있고 1단계 결정이 모두 반영됐다(위 대응 확인). 사용자가 다른 세션에서 검토하며 2.1·2.2를 추가했고, 이 세션 재검토에서 고친 2곳을 승인했다(2026-11-04 15:17)
  - 2.3 "팩 교체 구조" 근거를 `(1.3)`에서 `(requirements 1.3)`으로 고쳤다. design.md 1.3절과 헷갈렸다
  - 2.2 리전: botocore의 `AWS_REGION` 인식이 미확인이라 `region_name`으로 직접 넘기고 허용 리전 밖이면 시작 시 멈춘다고 적었다
- `design.md` 상태를 "확정"으로 바꿨다
