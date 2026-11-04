# 6 산출물 형식 정리 기록

상태: 완료(2026-11-04)
대상: [requirements.md](../../01-requirements/output/requirements.md), [design.md](../../02-spec-design/output/design.md)

## 입력

- 사용자 지적: 요구사항 정의서와 설계서의 내용이 아니라 정리된 형식이 마음에 들지 않는다. 각 단계의 최종 산출물이 된다.

## 진단

- 두 문서 모두 작업 과정(작성 단계, 사용자 지적, 내부 약어 출처)이 본문에 섞여 있었다. 용어 정의가 없었다.
- requirements.md: 요구사항 하나를 가리킬 ID, 우선순위, 검증 방법이 없었다. 일정·축소 기준, 미결 사항, 결정 목록 대조 같은 과정 내용이 들어 있었다.
- design.md: 1장이 결정 시점(이 단계, 3단계로 넘김, Seed가 넘김)으로 나뉘어 같은 주제(Bedrock, SQLite)가 여러 절에 흩어져 있었다. 8장 작업 단위와 모델 등급 권고는 구현 계획이었다. 요구사항 추적이 Seed 수용 기준 번호뿐이었다.

## 질문과 답

| 질문 | 답 |
| --- | --- |
| 양식 | 표준 양식 경량판. 요구사항은 ISO/IEC/IEEE 29148 SRS, 설계서는 arc42/IEEE 1016을 줄인 구조 |
| 과정 기록 위치 | dev-process로 옮기고 산출물에는 링크만 남긴다 |

## 결과

| 파일 | 변경 |
| --- | --- |
| requirements.md | 1.1. 개요·전체 설명·CR·FR·GR·NFR·완료 조건·부록 구조. 요구사항을 `FR-1.2`처럼 개별 ID로 나누고 우선순위(필수, 축소 대상)와 검증 방법을 붙였다. 기존 영역 ID(FR-1~10, GR-1~8, NFR-1~5)는 유지해 Seed 등의 참조가 그대로 맞는다. 출제 범위(옛 1.4, 1.5 출제 범위 밖)는 CR-1~CR-9가 되었다 |
| design.md | 1.1. 개요·아키텍처·스택·모듈·데이터·흐름·인터페이스·횡단 관심사·설계 결정(D-1~D-13)·추적표 구조. 옛 1장 결정을 주제별 절로 옮겼다. 결정의 대안은 [01-open-items.md](01-open-items.md) 질문 표에서 가져왔다 |
| [05-output.md](../01-requirements/05-output.md) | 새로 만듦. requirements.md에서 뺀 결정 출처, 일정·축소 기준, 미결 사항, 결정 목록 대조 |
| 이 파일 | design.md에서 뺀 작성 경위, 구현 작업 단위, 축소 적용 순서 |
| seed.yaml, page-allowlist.md, `input/README.md` | 옛 절 번호 참조를 새 위치로 고쳤다 |

내용은 바꾸지 않았다. 새로 쓴 것은 용어 정의, 우선순위·검증 방법 열, 설계 목표, 확인 필요 항목 모음, 문제 상태 도식, 풀이 순서 도식, 추적표다. 모두 기존 문장에서 끌어냈다.

추적표에서 GR-8(코드형 문제 재료 우선순위)에 대응하는 설계 절이 없음을 확인했다. 구현 때 생성 프롬프트에 반영할지 정한다.

## design.md에서 옮긴 내용

### 작성 경위

- 옛 1장(1.1, 1.2)은 계획 1단계([01-open-items.md](01-open-items.md))에서, 1.3절과 2~8장은 계획 4단계([04-design-modelchk.md](04-design-modelchk.md))에서 썼다.
- 옛 1.3절의 구현 값은 [seed.yaml](../../02-spec-design/output/seed.yaml) 제약 "구현 값은 design.md가 정한다"와 QA 자문 지적에서 왔다([03-seed.md](03-seed.md)).
- 2.1 아키텍처 개요와 2.2 기술 스택·실행 환경은 사용자 지적으로 추가했다(04-design-modelchk.md).
- 허용 목록은 계획 2단계([02-docs-mcp.md](02-docs-mcp.md))에서 다뤘다.

### 3단계로 넘긴 작업

옛 1.2절 "3단계에서 할 일" 열이다.

| 항목 | 3단계에서 할 일 |
| --- | --- |
| Bedrock 운영 | 첫 배치에서 요청 제한 발생 여부와 비용 확인 |
| React-FastAPI 연결 | 프록시 설정 |
| SQLite 운영 | 백업 위치와 보관 개수 |
| 생성 시간 | 측정과 일정 재확인. 2026-11-05 저녁 축소 기준([05-output.md](../01-requirements/05-output.md) A.3)과 대조 |

### 3단계 작업 단위와 수용 기준 대응

옛 8장이다. 3단계 계획의 입력이다.

수용 기준 번호는 [seed.yaml](../../02-spec-design/output/seed.yaml) `acceptance_criteria` 순서다. 1 풀, 2 감사, 3 3세트 풀이, 4 세트 출제, 5 풀이 화면, 6 채점, 7 복습 큐, 8 기준선 지표, 9 Langfuse.

등급·강도 열은 3단계 구현 작업을 맡는 코딩 에이전트에 대한 `modelchk` 권고다(2026-11-04). 등급은 fast·standard·frontier, 강도는 glance·measured·thorough·exhaustive다. 근거와 올리고 내릴 신호는 [04-design-modelchk.md](04-design-modelchk.md)에 있다. 앱이 부르는 Bedrock 모델(NFR-4)과 무관하다.

| # | 작업 단위 | 산출 | 수용 기준 | 의존 | 등급·강도 (`modelchk`) |
| --- | --- | --- | --- | --- | --- |
| W1 | 저장소 골격 | `app/`, `sandbox/`, `web/` 프로젝트, `0001_init.sql`, `migrate`, 백업 | 3 | - | fast · measured |
| W2 | 허용 목록 데이터와 스냅샷 | `allowlist.yaml`, `snapshots/`, `allowlist build` | 1 | W1 | standard · thorough |
| W3 | 결정적 검사 | `gates.py`와 테스트(정규화, 대조, Jaccard, 단답) | 1, 6 | W1 | fast · thorough |
| W4 | Bedrock·관측 래퍼 | `llm.py`(타임아웃, 재시도, 토큰·비용, Langfuse 선택), 단가표 | 8, 9 | W1 | standard · measured |
| W5 | 샌드박스 | `runner.py`, `fakes.py`, `sandbox_client.py`, lock 해시 | 1 | W1 | standard · thorough |
| W6 | 생성 파이프라인 | 그래프, 노드, 프롬프트, 슬롯 계획, 재개, `generate` | 1 | W2~W5 | frontier · thorough |
| W7 | 파일럿과 풀 생성 | 파일럿 6문제 측정, 60문제까지 배치, `pool freeze` | 1 | W6 | standard · thorough |
| W8 | 세트·채점·복습 | `sets.py`, `grading.py`, `review.py`와 테스트 | 4, 6, 7 | W1, W3 | standard · thorough |
| W9 | FastAPI | design.md 7.1 엔드포인트, 409 규칙 | 3~7, 2 | W8 | standard · measured |
| W10 | React UI | 풀이 화면, 결과·매핑·근거, 태그, 감사 화면 | 5, 3, 2 | W9 | standard · measured |
| W11 | 감사 | `audit.py`, 표본·시드, 결과 계산, 본인 감사 수행 | 2 | W7, W9, W10 | fast · measured |
| W12 | 변형 문제 | `generate --variants`, 복습 큐 연결 | 7 | W6, W8 | standard · measured |
| W13 | 기준선 지표 | `metrics.py`, `baseline.json` | 8 | W4, W7, W8 | fast · glance |
| W14 | 3세트 풀이와 재시작 확인 | 본인 3세트, 서버 재시작 뒤 SQLite 조회 스크립트 | 3 | W10, W11 | fast · glance |

축소 기준([05-output.md](../01-requirements/05-output.md) A.3, seed `scope_cut_waiver`)에 걸리면 W12를 먼저 빼고, 그다음 W4의 Langfuse 부분을 뺀다.
