# 03 EXP-1 실행 (Judge) 기록

상태: 진행 중
시작: 2026-11-05 16:42
완료:
계획: [04-prompt-model-experiments-plan.md](../04-prompt-model-experiments-plan.md)의 3단계
세션 모델: Opus 5.5(`claude-opus-5-5`). 추론 강도 미확인

## 입력

- 문항 목록: `data/experiments/EXP-1/items.json`(1단계에서 사용자가 라벨 확인)
- 변형: `data/experiments/EXP-1/variants/control/`, `data/experiments/EXP-1/variants/arena/`
- 앞 단계 인계: [01-harness.md](01-harness.md) "인계"의 사용자 대기 3건

## 진행

### 사용자 대기 3건 정리 (2026-11-05 16:42)

- (2) Haiku 4.5 단가: AWS Price List `AmazonBedrockFoundationModels` us-east-1 공표본(`publicationDate` 2026-10-12T08:40:08Z)에서 확인했다. 확인일 2026-11-05.
  - Global(`USE1-MP:USE1_InputTokenCount_Global-Units` 등): 입력 1.00, 출력 5.00 USD/1M
  - Regional: 입력 1.10, 출력 5.50 USD/1M
  - `data/pricing/bedrock.yaml`에 `global.`, `us.` 두 행을 더했다.
- 테스트: 행 추가 뒤 첫 `uv run pytest`는 17 failed, 356 passed였다(`test_api_schema.py` 포함). 바로 다시 돌리면 373 passed였다. `test_api_schema.py`만 따로 돌려도 18 passed다. 세 번째 전체 실행도 373 passed다. 첫 실패의 원인은 미확인이다.
- (1) 비용 재추정(확인한 Haiku 단가 반영, 모델 호출 없음):

| 항목 | 호출 | 입력 | 출력 | 비용(USD) |
| --- | --- | --- | --- | --- |
| Sonnet 4.5 실행 3회 | 231 | 약 510만 | 약 12만 | 약 17.1 |
| Haiku 4.5 실행 2회 | 154 | 약 340만 | 약 8만 | 약 3.8 |
| EXP-1 합 | 385 | | | 약 20.9 |
| EXP-2(계획 추정) | | | | 7~14 |
| 단계 합 | | | | 약 28~35 |

  단계 합의 상한이 결정 3(30 USD)을 넘을 수 있다.

### 사용자 답 (2026-11-05 16:45)

| 질문 | 답 |
| --- | --- |
| EXP-1 실행 범위 | 계획대로 5회. 첫 실행 뒤 실제 비용으로 다시 계산하고, 30 USD를 넘을 것 같으면 멈추고 묻는다 |
| `quiz experiment judge`의 `.env` 읽기 | 허용. CLAUDE.md "비밀과 환경"의 `.env` 줄과 "명령" 표를 고쳤다 |

### 1번: 일일 한도 확인 (2026-11-05 16:47)

- 리전 `us-east-1`. 호출 1회씩, 입력 14·출력 4토큰
- `global.anthropic.claude-sonnet-4-5-20250929-v1:0`: OK
- `global.anthropic.claude-haiku-4-5-20251001-v1:0`: OK

### 2번: `control`×Sonnet 4.5 (arm `control-s45`)

- 시작 2026-11-05 16:48. `QUIZ_PROMPTS_DIR=../data/experiments/EXP-1/variants/control`. 로그 `data/experiments/EXP-1/logs/control-s45.log`
- arm 이름 규칙: `<프롬프트>-<모델>[-r<반복>]`. `s45`는 Sonnet 4.5, `h45`는 Haiku 4.5다

## 인계

갱신: 2026-11-05 16:48
- 마지막 완료 작업: 1번 일일 한도 확인
- 다음 작업: `control-s45` 결과로 비용 재추정(2번 끝), 그다음 3번
- 실행 중: `control-s45`(로그 `data/experiments/EXP-1/logs/control-s45.log`, 결과 `data/experiments/EXP-1/control-s45.json`). 끊겼으면 같은 명령을 다시 돌리면 오류 없는 문항은 건너뛴다
- 사용자 대기: 없음
- 먼저 읽을 파일: 이 파일 "진행", 계획 3장 3단계

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| Haiku 4.5 단가 | Global 입력 1.00, 출력 5.00 USD/1M. Regional 1.10, 5.50 | 없음 |
| `experiment judge`의 `.env` | 사용자 승인(2026-11-05). CLAUDE.md를 고쳤다 | CLAUDE.md `.env` 규칙(01-harness.md 결정 표) |

## 계획과 다른 점

- 없음

## 끝나는 조건 확인

- 조건: 다섯 실행의 표가 `exp-1.md`에 있다. 판정이 기록됐다.
- 결과:
