# 04 EXP-2 생성 실행 기록

상태: 완료
시작: 2026-11-05 17:07(한도 확인 시각. 기록 파일은 그 직전에 만들었다)
완료: 2026-11-05 17:25 (사용자 확인 "승인")
계획: [04-prompt-model-experiments-plan.md](../04-prompt-model-experiments-plan.md)의 4단계
세션 모델: Opus 5.5(`claude-opus-5-5`), 추론 강도 미확인

## 입력

- 슬롯 목록: `data/experiments/EXP-2/slots.json`(12슬롯, 시드 20261105)
- 프롬프트: `data/experiments/EXP-2/variants/control/`, `data/experiments/EXP-2/variants/arena/`. 두 디렉토리는 `generate.md`만 다르다. `control`은 `packs/langchain/prompts/`와 같다(2026-11-05 `diff -rq` 확인)
- 고정 조건(계획 4단계): 생성 모델 NFR-4.1(`global.anthropic.claude-sonnet-4-6`), Judge는 `control` 프롬프트와 NFR-4.2(`global.anthropic.claude-sonnet-4-5-20250929-v1:0`), 같은 슬롯, 같은 스냅샷, 재생성 한도 3회, arm마다 빈 실험 DB
- 예산: 결정 3 상한 30 USD - EXP-1 17.73 USD = 12.27 USD

## 진행

### 1번: 일일 한도 확인 (2026-11-05 17:07)

- 리전 `us-east-1`. 호출 1회씩, 입력 9·출력 4토큰
- `global.anthropic.claude-sonnet-4-6`(생성): OK
- `global.anthropic.claude-sonnet-4-5-20250929-v1:0`(Judge): OK
- 코드형 슬롯용 샌드박스 가상 환경 `sandbox/.venv/Scripts/python.exe`가 있다

### 2번: `control` 첫 2슬롯 (2026-11-05 17:08 시작)

- 명령: `QUIZ_DB=../data/experiments/EXP-2/control.db QUIZ_PROMPTS_DIR=../data/experiments/EXP-2/variants/control uv run quiz generate --slots ../data/experiments/EXP-2/slots.json --count 2`
- 로그 `data/experiments/EXP-2/logs/control-1.log`
- 첫 2슬롯은 둘 다 `rag` 버킷(single, multi)이다. 코드형 슬롯 단가는 이 실측에 들어가지 않는다
- 나머지 10슬롯은 `data/experiments/EXP-2/slots-3-12.json`(`slots.json`의 3~12번)으로 같은 DB에 두 번째 배치를 돈다. arm DB 하나에 배치 두 개가 생긴다. summary는 DB 전체를 센다
- 끝: 2026-11-05 17:10:43. 배치 `b20261105-01`. 2슬롯 모두 passed(regen 1, 2). 걸린 시간 130초
- 실측(`quiz experiment summary --exp EXP-2`): 첫 시도 `quote_match` 0/2, `quote_mismatch` 뒤 재시도 통과 2/3, Judge 통과율 1.0, T2.11 실패 0, 비용 1.287 USD, passed당 0.644 USD
- 시도 5번(1+1, 1+2)에 1.287 USD이므로 시도당 약 0.257 USD다. 03 파일럿 슬롯당 0.286 USD보다 슬롯당 2.25배다. 재생성 때문이다

#### 비용 재추정 (실측 반영, 2026-11-05 17:12)

시도당 0.257 USD로 계산했다. 슬롯당 시도 수는 1(재생성 없음)에서 4(한도 3회)까지다.

| 항목 | 낮게(슬롯당 1.8시도) | 높게(슬롯당 2.5시도, 이번 실측) | 근거 |
| --- | --- | --- | --- |
| `control` 첫 2슬롯 | 1.29 | 1.29 | 실측 |
| `control` 나머지 10슬롯 | 4.6 | 6.4 | 낮게는 03 첫 시도 실패율(116/209)에서 잡은 평균 |
| `arena` 12슬롯 | 4.0(슬롯당 1.3시도) | 7.7 | `arena`가 인용을 더 잘 복사하면 낮아진다 |
| EXP-2 합 | 약 9.9 | 약 15.4 | |
| 단계 합(EXP-1 17.73 포함) | 약 27.6 | 약 33.1 | |

높은 쪽이 결정 3(30 USD)을 넘는다. 남은 예산 12.27 USD로는 높은 쪽 15.4 USD를 덮지 못한다. 계획대로 멈추고 사용자에게 묻는다.

#### 사용자 답 (2026-11-05 17:14)

- arm마다 6슬롯(`slots.json` 1~6번)만 돈다. 6슬롯은 형식 4종(single, multi, short, code)과 버킷 3개(`rag`, `langgraph_basics`, `tool_mcp`)를 덮는다
- 추정: EXP-2 약 6.5~8 USD, 단계 합 약 24~26 USD
- 판정 기준(계획 4단계)은 바꾸지 않는다. 표본이 작아 결과는 방향으로만 쓴다

### 3번: `control` 3~6번, `arena` 1~6번 (2026-11-05 17:15 시작)

- `control`: `slots-3-6.json`(`slots.json` 3~6번)으로 `control.db`에 두 번째 배치. 로그 `logs/control-2.log`
- `arena`: `slots.json --count 6`으로 `arena.db`. 로그 `logs/arena.log`
- 같은 생성 모델 한도를 나눠 쓰므로 두 arm을 차례로 돈다. 스로틀이 arm 사이 차이를 만들지 않게 하려는 것이다
- 끝: `control` 2026-11-05 17:16:39(배치 `b20261105-02`, 4슬롯 passed, regen 0·1·1·1, 1.042 USD), `arena` 17:19:04(배치 `b20261105-01`, 6슬롯 passed, regen 1·0·0·0·0·0, 1.387 USD). 미완료 0
- 백그라운드 명령은 exit 1로 끝났다. 원인은 마지막 `tail -8 <파일 둘>`의 옵션 오류다. 두 `quiz generate`는 모두 exit 0이다

### 4·5번: summary와 `exp-2.md` (2026-11-05 17:21)

- `quiz experiment summary --exp EXP-2`로 표를 냈다. 표와 판정은 [exp-2.md](../../04-prompt-model-experiments/output/exp-2.md)에 썼다(초안)
- EXP-2 실제 비용 합 3.72 USD(`control` 2.33, `arena` 1.39). 추정 6.5~8 USD보다 낮다. 단계 합은 21.45 USD다(EXP-1 17.73 포함, 한도 확인 호출은 무시할 만하다)
- 판정: `arena`는 고정 기준으로 채택 후보다(첫 시도 `quote_match` 5/6 > 2/6, passed 6 = 6, passed당 0.231 < 0.388 USD, Judge 통과율과 T2.11 실패는 나빠지지 않았다)
- summary 표 밖에서 확인한 것: `verification_results`를 슬롯별로 읽었다. `arena`가 나빠진 슬롯은 없다. `control` Judge 실패 1건(`b20261105-02-003`, `@tool` single)은 `judge_fail:answer_key_correct`이고 인용은 맞았다

### 6번: Langfuse 사용량

- 사용량 화면은 브라우저에서 사용자가 본다. 사용자에게 요청했다
- Langfuse 기록은 `quiz generate` 배치만 남긴다(`app/quiz/batch.py:48`의 `llm.trace_config`). `quiz experiment judge`는 붙이지 않는다. EXP-1은 Langfuse에 남지 않았다(코드 확인, 2026-11-05)
- 위험: 실험 DB 배치 ID(`b20261105-01`, `-02`)가 `data/quiz.db`의 03 운영 배치 ID와 같다. Langfuse 세션 ID와 태그가 배치 ID이므로 둘이 섞인다. 실험 trace는 시간(2026-11-05 08:08~08:20Z)으로만 가린다
- 사용자가 보낸 화면(2026-11-05, "Langfuse Cost Dashboard", Env `default`): Traces 129, Observations 6.83K, 비용 합 41.68 USD. 그래프 축이 2026-11-04 17:00~2026-11-05 17:00대라 지난 24시간 범위로 보인다. 03 배치와 EXP-2가 함께 들어 있다
  - 24시간 사용량은 약 6,960 units(trace + observation. score 수는 미확인)다. Hobby 월 5만 units 대비 약 14%다. 한도 부족은 없다
  - EXP-2만의 사용량은 이 화면으로 나누지 못한다. 미확인이다

## 인계

갱신: 2026-11-05 17:25
- 마지막 완료 작업: 4단계 전체. `exp-2.md` 사용자 승인, 확정
- 다음 작업: 5단계(`05-mandela.md`). 실험 배치 ID와 운영 배치 ID가 겹치는 문제를 타당성 위협 재료로 넘긴다. 단계 비용 합 21.45 USD(상한 30 USD)
- 실행 중: 없음
- 사용자 대기: 없음
- 먼저 읽을 파일: 이 파일 "진행", `03-exp1-judge.md` "진행", 계획 3장 5단계
- 먼저 읽을 파일: 이 파일 "진행", 계획 3장 4단계

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 첫 2슬롯 분리 실행 | `--count 2`로 첫 배치를 돌리고, 나머지는 `slots-3-6.json`으로 두 번째 배치를 돈다. 하네스에 시작 위치 옵션이 없어서다. `arena`는 6슬롯을 한 배치로 돈다 | 없음(계획 4단계 2번의 실행 방식) |
| EXP-2 6슬롯 | 사용자 선택(2026-11-05 17:14). arm마다 `slots.json` 1~6번만 돈다. 비용 재추정 높은 쪽이 결정 3을 넘어서다 | 계획 4단계 "같은 슬롯 목록" 12슬롯 |

## 계획과 다른 점

- arm마다 12슬롯이 아니라 6슬롯을 돈다(사용자 선택, 비용). 계획 상단 "수정:" 줄

## 끝나는 조건 확인

- 조건: 두 arm의 summary 표가 `exp-2.md`에 있다. 판정이 기록됐다.
- 결과(2026-11-05 17:25): 충족. 두 arm(6슬롯씩, 사용자 선택)의 summary 표와 판정이 `exp-2.md`에 있다. Langfuse 사용량을 기록했다(EXP-2만의 값은 미확인). 사용자가 승인했다
