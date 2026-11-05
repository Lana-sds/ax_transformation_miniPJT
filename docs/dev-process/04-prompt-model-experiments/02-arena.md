# 02 arena 방법으로 변형 만들기 기록

상태: 진행 중
시작: 2026-11-05 16:10 이후(분 미확인)
완료:
계획: [04-prompt-model-experiments-plan.md](../04-prompt-model-experiments-plan.md)의 2단계
세션 모델: Opus 5.5(`claude-opus-5-5`), 추론 강도 미확인

## 입력

- 대조군: `packs/langchain/prompts/` 전체를 `data/experiments/EXP-1/variants/control/`, `data/experiments/EXP-2/variants/control/`에 복사했다(2026-11-05).
- 기준선 실패 이유: 계획 1.1, [05-m4.md](../03-implementation/05-m4.md) "7·8회차 `quote_mismatch` 원인"

## 진행

### A. 과제 정의 (2026-11-05)

- EXP-1: `data/experiments/EXP-1/arena/task.md`. Judge 파일(`judge.md`, `judge/*.md`)만 고친다. `explanation_correct` 항목을 더한다(결정 6). 결함 유형(해설 오류, 단서, 인용 무관, 모호)을 일반 문장과 가상의 예로 적었다. 감사 메모와 데이터셋 파일, `data/quiz.db`, `data/crosscheck/`는 열지 못하게 했다.
- EXP-2: `data/experiments/EXP-2/arena/task.md`. `generate.md`와 필요할 때만 `formats/`, `quality/`를 고친다. 05-m4.md에서 확인한 두 원인(링크 벗김, 코드 펜스 속성 생략)을 적었다. `slots.json`, `data/quiz.db`는 열지 못하게 했다.
- 공통 제약(후보에게 준다): 출력 스키마 유지, T2.11 문구 유지, 문제 영어·해설 한국어·근거는 원문 인용, 고친 파일 길이 1.3배 이하, 자리표시자 유지.

채점 기준(후보에게 주지 않는다. D 단계 기반 고르기에 쓴다):

| 실험 | 기준 |
| --- | --- |
| 공통 | 1. 공통 제약을 모두 지킨다. 2. 지시가 판정 가능한 검사로 쓰여 있다(모델이 항목마다 참/거짓을 정할 수 있다). 3. 정상 문항을 떨어뜨릴 새 조건(지나치게 넓은 거짓 조건)이 없다 |
| EXP-1 | 4. `explanation_correct`가 보기별 해설과 보기의 대응, 해설 사실의 문서 일치를 따로 본다. 5. 단서 검사가 지문 쪽 정답 노출(지문 코드·문구)을 덮는다. 6. 인용마다 정답과의 관련을 본다 |
| EXP-2 | 4. 링크·코드 펜스·표 행을 원문 그대로 복사하라는 지시가 생성 시점에 있다. 5. 마크다운 없는 문장을 고르는 대안을 준다. 6. 인용 선택과 복사 절차가 짧다(지시 길이가 품질 규칙을 밀어내지 않는다) |

### B. 후보 (2026-11-05)

- EXP-1 후보 2개, EXP-2 후보 2개를 백그라운드 서브에이전트로 한 메시지에서 띄웠다. 후보는 과제 정의 파일 경로만 받았다. 출력은 `data/experiments/<EXP-n>/arena/candidate-<k>/`다.
- 2026-11-05 네 후보가 끝났다. 모두 금지 목록을 열지 않았다고 보고했다. 모델 호출은 없다.

| 후보 | 바꾼 파일 | 길이 비율 | 요지 |
| --- | --- | --- | --- |
| EXP-1 c1 | `judge.md`, `judge/choice.md`, `judge/short.md` | 1.290 | `explanation_correct` 추가. 모호는 `answer_key_correct`, 무관 인용은 `quote_supports_answer`에 거짓 조건 추가. `no_cue` 시험 5(지문 노출), 6(정답만 문서 문장 복사). 단답 지문 노출은 `answer_key_correct`로 |
| EXP-1 c2 | 위 셋과 `judge/code.md` | 1.291 | c1과 같은 모양. 더한 것: 답 키를 보기 전에 먼저 풀게 한다. 모호는 `distractors_wrong`. 해설이 문서에 "없는" 내용만으로는 실패가 아니고 "어긋날" 때만 실패. 코드형은 해설이 자기 `exec_predictions`와 다르면 실패. 단답은 다른 문서 용어도 맞으면 실패 |
| EXP-2 c1 | `generate.md` | 1.28 | 새 `## Quotes` 절(검사 방식 설명, 평문 선호, 링크·마크업 그대로, 펜스 줄 빼기, 고쳐 쓰기 금지). 문서 뒤에 "인용을 찾아 한 글자씩 대조" 한 줄 |
| EXP-2 c2 | `generate.md` | 1.293 | 규칙 3을 하위 목록으로 풀었다(30~300자, 한 문단 안, 보통 한 문장). HTML 태그·엔티티 유지, 마침표 추가 금지. 문서 뒤 `## Before you answer` 절(다르면 다시 복사하거나 평문 문장 고르기) |

두 실험 모두 후보가 같은 모양으로 모였다. arena 규칙대로 모인 모양을 쓰고 과제 정의는 고치지 않았다.

### C. 교차 Judge (생략)

- 서브에이전트는 Claude 계열만 쓸 수 있다. 부모와 다른 계열의 교차 Judge를 부를 수 없어 건너뛰었다(SKILL.md 규칙, 계획 4장). 변형 판정은 3, 4단계 측정이 한다.

### D·E. 합성 노트 (2026-11-05)

EXP-1 → `data/experiments/EXP-1/variants/arena/`

- 기반: c2. 채점 기준 3(지나치게 넓은 거짓 조건 없음)에서 앞선다. c1의 `explanation_correct`는 "문서가 말하지 않는 동작을 말하면 거짓"이라 정상 해설의 보충 설명까지 떨어뜨릴 수 있다. c2는 "어긋날 때만"이다. c2는 코드형 해설과 실행 예측의 대조, 단답 모호까지 덮는다(기준 4, 6).
- 옮긴 것: c1의 `no_cue` 시험 6 표현 "nearly word for word"(c2는 "verbatim"). 실제 결함 유형 "정답 보기가 문서 문장을 거의 그대로 옮김"을 c2 표현이 놓칠 수 있다.
- 버린 것: c1의 모호 조건 위치(`answer_key_correct`). c2는 `distractors_wrong`에 두었다. 선택형에서 "다른 보기도 옹호된다"는 오답 항목의 뜻과 맞다. 단답은 c2도 `answer_key_correct`에 둔다.
- 길이: Judge 파일 4개 합 3655 → 4732바이트, 1.295. 줄바꿈은 대조군처럼 CRLF로 맞췄다(`sed -i`가 LF로 바꾼 것을 되돌렸다).

EXP-2 → `data/experiments/EXP-2/variants/arena/`

- 기반: c2. 문서 뒤 대조 절에 "다르면 다시 복사하거나 평문 문장을 고르라"는 행동이 있다(기준 4, 5). HTML 태그·엔티티와 마침표 추가를 덮는다. 규칙 3 안에 있어 따로 찾을 절이 없다(기준 6).
- 옮긴 것: c1의 링크 반례 "(never `` `Name` `` alone)". 확인한 원인 1(링크 벗김)을 직접 막는다.
- 버린 것: c2의 "30~300자, 한 문단 안, 보통 한 문장". 인용이 짧아지면 Judge `quote_supports_answer` 근거가 약해질 수 있다(c2 보고서의 위험). 대조군의 "보통 한두 문장"으로 되돌렸다. 인용 검사에는 상한이 없다.
- 길이: `generate.md` 2381 → 3034바이트, 1.274.

### F. 검증 (W1 병합 `308579c` 뒤)

- EXP-1 `variants/arena/judge_items.json`을 더했다. `explanation_correct` 하나, 형식 4종 모두. 설명은 `judge.md`의 항목 문장을 줄인 것이다. `judge.md`에는 `{{extra_items}}` 자리표시자를 넣지 않았다. 항목은 본문에 이미 문장으로 있다.
- `QUIZ_PROMPTS_DIR`을 바꿔 `tests/test_quality.py`, `test_judge.py`, `test_generate.py`, `test_pipeline_loop.py`(75개)를 돌렸다.

| 디렉토리 | 결과 |
| --- | --- |
| `EXP-1/variants/control` | 75 passed |
| `EXP-2/variants/arena` | 75 passed. T2.11 문구 테스트 포함 |
| `EXP-1/variants/arena`(`judge_items.json` 있음) | 43 passed, 32 failed. 실패는 모두 `ValidationError for JudgeVerdict`다. 기존 테스트의 가짜 Judge 응답에 새 필수 필드 `explanation_correct`가 없다. 프롬프트 문구 때문이 아니다 |
| `EXP-1/variants/arena`(`judge_items.json`을 잠시 뺌) | 75 passed. Judge 프롬프트 문구 테스트(항목 이름 백틱 표기, 남는 `{{` 없음) 포함 |

- 새 항목의 스키마·실패 이유 경로는 `tests/test_experiments.py`가 확인한다(병합 뒤 355 passed에 포함).

## 인계

갱신: 2026-11-05 16:35
- 마지막 완료 작업: A~F
- 다음 작업: 사용자 완료 확인 뒤 "완료"로 바꾼다
- 실행 중: 없음
- 사용자 대기: 2단계 완료 확인
- 먼저 읽을 파일: 이 파일, 각 `candidate-<k>/NOTES.md`

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 후보 수 | 실험마다 2개(계획대로) | 없음 |

## 계획과 다른 점

- 합성 노트는 별도 파일이 아니라 이 기록의 "D·E. 합성 노트" 절에 두었다.
- F에서 EXP-1 변형은 `judge_items.json`을 뺀 상태로 문구 테스트를 통과시켰다. 기존 테스트 가짜 응답이 새 필수 필드를 모르기 때문이다.

## 끝나는 조건 확인

- 조건: 실험마다 `variants/control/`, `variants/arena/`와 합성 노트가 있다. 프롬프트 문구 테스트가 변형에서도 통과한다.
- 결과(2026-11-05 16:35): 충족. 두 실험 모두 `variants/control/`, `variants/arena/`가 있다. 합성 노트는 위 D·E 절이다. 문구 테스트는 F 표대로 통과했다.
