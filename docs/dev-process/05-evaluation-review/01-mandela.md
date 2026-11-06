# 01 mandela 기록

상태: 진행 중
시작: 2026-11-06 09:11
완료:
계획: [05-evaluation-review-plan.md](../05-evaluation-review-plan.md)의 0단계, 1단계
세션 모델: Opus 5.5(`claude-opus-5-5`). 추론 강도: 미확인(세션 안에서 읽지 못함)

## 입력

- 0단계: 계획 0단계 1~7번
- 1단계: 계획 1장(평가 대상), 3장 2단계와 3단계 방법, 미리 아는 위협 3개

## 진행

### 0단계: 사전 준비

| 번호 | 한 일 | 결과 |
| --- | --- | --- |
| 1 | 결정 1~3 | 계획 상태 줄에 2026-11-06 승인으로 닫혀 있다 |
| 2 | 04 worktree에서 복사 | `.env`, `data/quiz.db`, `data/experiments/EXP-2/arena.db`, `control.db`. 네 파일 모두 `.gitignore`가 뺀다(`git check-ignore`). `data/quiz.db` sha256 `89fa897d…bbde`가 원본과 같다 |
| 3 | 설치 | `app/` `uv sync`, `sandbox/` `uv sync`, `web/` `npm ci`(취약점 0) |
| 4 | 테스트 | `cd app && uv run pytest -q`: 374 passed, 13 warnings(langsmith `asyncio.iscoroutinefunction` 사용 중단 경고), 39.16s. 1회 실행으로 통과했다 |
| 4 | 빌드 | `cd web && npm run build`: 종료 코드 0, `dist/assets/index-xVy1a_vr.js` 235.28 kB |
| 4 | lint | `cd web && npm run lint`(oxlint): 종료 코드 0. 경고 1개 `src/App.tsx:78:18 react(set-state-in-effect)` |
| 5 | `data/quiz.db` 행 수(읽기 전용 `mode=ro`) | 아래 표 |
| 6 | 평가 대상 커밋 | 아래 "평가 대상 커밋" |
| 7 | 세션 모델 | 상단에 적었다 |

`data/quiz.db` 행 수(2026-11-06 09:13):

| 테이블 | 행 |
| --- | --- |
| attempts | 41 |
| audit_records | 20 |
| audits | 1 |
| batch_slots | 122 |
| batches | 15 |
| grounding_records | 212 |
| pool_snapshot_items | 122 |
| pool_snapshots | 3 |
| questions | 117 |
| quiz_sets | 10 |
| review_items | 21 |
| schema_version | 2 |
| verification_results | 209 |

### 평가 대상 커밋

계획, 입력 README, 이 기록을 커밋한 해시를 적는다(아래 "인계").

### 1단계: mandela

(진행 중)

## 인계

갱신: 2026-11-06 09:14
- 마지막 완료 작업: 0단계 1~5, 7번
- 다음 작업: 0단계 6번 커밋, 1단계 `mandela` 서브에이전트
- 실행 중: 없음
- 사용자 대기: 없음
- 먼저 읽을 파일: 이 파일, 계획 3장

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| - | - | 없음 |

## 계획과 다른 점

- 없음

## 끝나는 조건 확인

- 조건: 점검 결과와 반영 여부가 기록됐다.
- 결과: 미확인(진행 중)
