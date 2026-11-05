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
- 끝: 2026-11-05T07:51:03Z(결과 파일 `updated_at`). 77문항, 오류 0, 스로틀 0
- 실측: 호출당 입력 27,336, 출력 250토큰, 0.0858 USD, 지연 6.4초. 합 6.61 USD. 예비 추정의 호출당 입력 2만보다 37% 많다
- 결과(`quiz experiment summary --exp EXP-1`): 실제 결함 0/18 검출. 주입 결함 13/24(정답 키 6/6, 단서 5/6, 인용 무관 2/6, 해설 오류 0/6). 정상 오탈락 0/35(감사 정상 0/3, 교차 풀이 정상 0/32)

#### 비용 재추정 (실측 반영, 2026-11-05 16:53)

| 항목 | 근거 | 비용(USD) |
| --- | --- | --- |
| `control-s45` | 실측 | 6.61 |
| `arena-s45`, `control-s45-r2` | 실측 호출당 단가. `arena`는 프롬프트가 조금 길어 7.0으로 잡음 | 약 13.6 |
| `control-h45`, `arena-h45` | 실측 토큰 × Haiku 단가(입력 1.00, 출력 5.00) | 약 4.4 |
| EXP-1 합 | | 약 24.6 |
| EXP-2 | 계획 추정 | 7~14 |
| 단계 합 | | 약 32~39 |

단계 합이 결정 3(30 USD)을 넘는다. 계획대로 멈추고 사용자에게 묻는다.

#### 사용자 답 (2026-11-05 16:55)

- 반복 실행(`control-s45-r2`)을 빼고 진행한다. EXP-1 약 18 USD, 단계 합 약 25~32 USD다.
- EXP-2가 30 USD 쪽으로 가면 EXP-2 첫 2슬롯 뒤 다시 묻는다.

#### 판정 기준 고침 (나머지 실행 전에 고정, 2026-11-05 16:56)

- `arena`가 실제 결함 검출 수가 더 많고, 정상 오탈락이 2개 이하이면 채택 후보다.
- 반복 실행이 없어서 "차이가 뒤집힘 수보다 큰가"는 판단하지 않는다. 차이는 방향으로만 쓴다.
- 예비 모델 기준은 그대로다. 검출률이 NFR-4.2와 같거나 높을 때만 교체 제안을 기록한다.

### 3번: 나머지 3회 (2026-11-05 16:57 시작)

- Sonnet 줄: `arena-s45`. Haiku 줄: `control-h45` → `arena-h45`. 두 줄은 모델별 한도가 따로라서 동시에 돌린다. 줄 안에서는 차례로 돈다.
- 로그 `data/experiments/EXP-1/logs/<arm>.log`
- 끝: 세 arm 모두 77문항, 오류 0, 스로틀 0. 2026-11-05 16:58 전후(분 단위 미확인)

### 4·5번: summary와 `exp-1.md` (2026-11-05 16:58)

- `quiz experiment summary --exp EXP-1 --compare control-s45,arena-s45`로 표를 냈다. 표와 판정은 [exp-1.md](../../04-prompt-model-experiments/output/exp-1.md)에 썼다(초안).
- EXP-1 실제 비용 합 17.73 USD. 결정 3 상한 30 USD까지 EXP-2에 12.27 USD가 남는다.
- 판정: `arena-s45`는 고정 기준으로 채택 후보다(실제 결함 1 > 0, 오탈락 1). 예비 모델 교체는 제안하지 않는다.
- summary 표를 그대로 옮기지 않고 확인한 것:
  - `explanation_correct`는 `arena-s45` 9문항, `arena-h45` 12문항에서 거짓이었다. 해설 오류 10문항에서는 한 번도 거짓이 아니었다.
  - `arena-h45`의 실제 결함 검출 1건(`real-04-009`)은 `judge_fail:schema_invalid`였다. `exp-1.md`에 빼고 읽도록 적었다.
- 테스트 출력 인코딩: Windows 콘솔(cp949)에서 판정 JSON의 이모지 출력이 `UnicodeEncodeError`를 냈다. `PYTHONIOENCODING=utf-8`로 다시 봤다. 하네스 문제는 아니다.

## 인계

갱신: 2026-11-05 16:59
- 마지막 완료 작업: 4회 실행, summary, `exp-1.md` 초안
- 다음 작업: 사용자 확인 뒤 이 기록을 "완료"로 바꾸고 4단계(EXP-2). EXP-2 남은 예산 12.27 USD
- 실행 중: 없음
- 사용자 대기: 3단계 끝나는 조건 확인(`exp-1.md` 초안 검토)
- 먼저 읽을 파일: 이 파일 "진행", 계획 3장 3단계

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| Haiku 4.5 단가 | Global 입력 1.00, 출력 5.00 USD/1M. Regional 1.10, 5.50 | 없음 |
| 반복 실행 제외 | 사용자 선택(2026-11-05). 판정 기준에서 뒤집힘 비교를 뺐다 | 계획 3단계 arm 5회, 판정 기준 |
| `experiment judge`의 `.env` | 사용자 승인(2026-11-05). CLAUDE.md를 고쳤다 | CLAUDE.md `.env` 규칙(01-harness.md 결정 표) |

## 계획과 다른 점

- `control`×NFR-4.2 반복 실행을 뺐다(사용자 선택, 비용). EXP-1은 4회다. 계획 상단 "수정:" 줄

## 끝나는 조건 확인

- 조건: 다섯 실행의 표가 `exp-1.md`에 있다. 판정이 기록됐다.
- 결과(2026-11-05 16:59): 사용자 선택으로 실행은 4회다. 네 실행의 표와 판정이 `exp-1.md`에 있다. 사용자 확인 대기
