# 05 mandela 기록

상태: 완료
시작: 2026-11-05 17:28
완료: 2026-11-05 17:36 (사용자 확인 "확인 완료")
계획: [04-prompt-model-experiments-plan.md](../04-prompt-model-experiments-plan.md)의 5단계
세션 모델: Opus 5.5(`claude-opus-5-5`), 추론 강도 미확인

## 입력

- 실험 설계: 계획 1.2, 3장 3·4단계
- 데이터셋 구성: [01-harness.md](01-harness.md) 1-나, `data/experiments/EXP-1/items.json`, `data/experiments/EXP-2/slots.json`
- 변형 작성: [02-arena.md](02-arena.md)
- 결과: [exp-1.md](../../04-prompt-model-experiments/output/exp-1.md), [exp-2.md](../../04-prompt-model-experiments/output/exp-2.md)
- 4단계에서 넘긴 위협: 실험 DB 배치 ID(`b20261105-01`, `-02`)가 `data/quiz.db`의 03 운영 배치 ID와 같다. Langfuse 세션 ID와 태그가 섞인다

## 진행

### 1번: `mandela` 누수 점검 (2026-11-05 17:30)

- 호출: Skill `mandela`, 인자 "EXP-1(Judge 프롬프트 A/B)와 EXP-2(생성 프롬프트 A/B)를 점검한다. 근거: 계획 1.2·3장 3·4단계, 01~04 기록, exp-1.md, exp-2.md". 이 세션(실험 설계자)이 같은 세션에서 돌렸다. 독립 감사자(맥락 없는 서브에이전트)는 띄우지 않았다
- 추가로 읽은 것: `data/experiments/EXP-1/arena/task.md`(후보에게 준 과제 정의)

#### 뿌리

EXP-1은 Judge가 새로 보는 차원(해설, 단서, 인용 관련성)에서 독립 정답이 없다. 문항은 모두 `control` Judge가 03에서 통과시킨 것이다. 라벨은 감사자 한 명과 설계자가 만들었다. EXP-2의 주 지표 `quote_match`는 스냅샷 원문과 바이트 대조라서 외부 정답이 독립적으로 들어온다.

#### 해당한 누수 유형

| 실험 | 유형 | 내용 | 결과에 미치는 방향 | 독립성 보완안 |
| --- | --- | --- | --- | --- |
| EXP-1 | 4. Tautology(대조군이 고른 문항) | 실제 결함 18과 정상 35는 모두 고정 풀 문항이다. 03에서 같은 `control` 프롬프트와 Sonnet 4.5가 통과시켰다. 그래서 `control-s45`의 실제 결함 검출 0과 오탈락 0은 구성으로 정해진다 | 실제 결함: `arena`가 하나만 잡아도 우위가 된다(`arena`에 유리). 오탈락: `arena`만 흔들림을 진다(`arena`에 불리) | Judge 전 단계의 시도(03에서 Judge가 떨어뜨린 시도 포함)에서 표본을 뽑는다. arm을 모르는 사람이 라벨을 붙인다 |
| EXP-1 | 2. Wrong null hypothesis(정상 묶음이 정상이 아님) | `crosscheck_clean` 32는 두 모델이 정답 키와 일치한 것만 확인했다. 해설, 단서, 인용 관련성은 확인하지 않았다. 감사 표본 20개 중 내용 지적이 없는 문항은 3개였다. `arena`가 오탈락시킨 `norm-03-007`(`arena-s45`)과 `arena-h45`의 2개는 실제 결함일 수 있다 | 오탈락 수를 해석할 수 없다. `arena`에 불리할 수 있다 | 오탈락 문항 3개와 무작위 정상 문항을 arm을 모르는 상태에서 모든 차원으로 다시 본다 |
| EXP-1 | 5. Verifier = designer(수집 방법이 샌다) | 후보에게 `items.json`은 숨겼다. 그러나 `task.md`의 예가 실제 결함 문항을 풀어 쓴 것이다(`03-021` "다른 보기를 반박", `05-007` "지문 코드에 정답", `04-017` "함수 이름을 풀어 씀", `01-001` "정답만 문서 문장", `01-002` "부재 논증"). 주입 `explanation_error` 방법도 같은 사람이 같은 예로 만들었다. 판정 기준도 `control-s45` 결과를 본 뒤(16:56) 고쳤다. 비용 때문에 반복 실행을 뺀 결과다 | 실제 결함과 주입 결함 모두 `arena`에 유리하다. 그런데도 `arena`의 해설 오류 검출은 0/10, 실제 결함 검출은 1/18이다 | 과제 정의에 적지 않은 결함 유형을 따로 둔다. 주입 방법은 과제 정의를 쓰지 않은 사람이 정한다 |
| EXP-2 | 3. Shared hallucination(같은 계열끼리 확인) | 생성은 Sonnet 4.6, Judge는 Sonnet 4.5다. 판정 기준 중 "passed 수"와 "Judge 통과율"은 같은 계열 모델의 확인이다. `arena`는 "평문 문장을 고르라"고 해서 인용이 정답과 덜 관련될 수 있다. 이것을 보는 것은 같은 계열 Judge의 `quote_supports_answer`뿐이다 | 주 지표(`quote_match`)에는 영향이 없다. 보조 기준만 약하다 | `arena` 6문항을 다른 계열(Nova Pro, gpt-oss-120b)로 교차 풀이하거나 사람이 인용 관련성을 본다 |

해당하지 않은 유형: 1(문서를 입력으로 주고 판정한다. 외워서 답할 대상이 아니다), 7·8(측정 대상이 사람이 아니다). EXP-2의 `quote_match`에는 4, 5가 해당하지 않는다. `arena`가 검사 방식에 맞춰 만들어졌지만 그 검사가 곧 요구사항(원문 그대로 인용)이다.

누수 유형은 아니지만 기록할 것: 실험 배치 ID(`b20261105-01`, `-02`)가 운영 배치 ID와 같다. summary는 arm DB만 읽으므로 결과 수치에는 영향이 없다. Langfuse trace는 시간으로만 가린다.

#### 계획에서 미리 적은 위협과 대조

| 계획의 위협 | 점검 결과 |
| --- | --- |
| 정상 문항은 `control`×NFR-4.2가 통과시킨 문항이다 | 해당(4). 실제 결함 18도 같다. 계획은 정상 문항만 적었다 |
| 실제 결함 라벨은 감사자 한 명의 메모다 | 해당(5에 묶음) |
| 변형 작성자가 감사 메모를 읽었다 | 해당(5). 과제 정의 예가 특정 문항을 풀어 쓴 수준이다 |
| 계획 밖 | 2(정상 묶음이 새 차원에서 확인되지 않음), EXP-2의 3(같은 계열 Judge), 판정 기준을 대조군 결과 뒤에 고친 시점 |

#### 이 점검 자체의 한계

- 점검자가 실험 설계자다(5). 독립 감사자를 띄우지 않았다.
- 위 표의 사실(문항 출처, `task.md` 문구, 기준 고친 시각, 감사 표본 수)은 기록 파일과 `task.md`에서 다시 확인할 수 있다.
- 미확인: 03 운영 Judge 입력과 `quiz experiment judge`가 다시 만든 입력이 같은지. 같다면 03 운영 판정은 `control-s45`의 반복 실행 하나로 볼 수 있다(`real-03-010`은 `control`이 두 번 통과시켰다).

#### 결론이 바뀌는가

| 실험 | 고정 기준 판정 | 누수 반영 | 바뀌는가 |
| --- | --- | --- | --- |
| EXP-1 | `arena` 채택 후보(실제 결함 1 > 0, 오탈락 1 ≤ 2) | 1 > 0의 0은 구성으로 정해졌다. 오탈락 1은 실제 결함일 수 있다. 누수가 `arena`에 유리한데도 해설 오류 0/10이다 | 판정 근거가 약해진다. 결론 바뀜 가능. 사용자에게 보인다 |
| EXP-2 | `arena` 채택 후보 | 주 지표는 독립이다. 보조 기준만 약하다 | 바뀌지 않는다 |

### 2·3번: 결론 변화와 채택 (2026-11-05 17:40)

| 질문 | 추천 | 사용자 답 |
| --- | --- | --- |
| EXP-1 `arena` Judge(`explanation_correct` 포함)를 운영에 반영하는가 | 보류 | 보류 |
| EXP-2 `arena` `generate.md`를 운영에 반영하는가 | 채택 | 채택 |

### 4번: 반영 (2026-11-05 17:42)

- `data/experiments/EXP-2/variants/arena/generate.md`를 `packs/langchain/prompts/generate.md`로 바이트 그대로 복사했다. sha256 `62c2e0b483e18051c4c0145db5cfa34ed4137c8789538a1bea98a7180304f229`(두 파일 같음). 나머지 프롬프트 파일은 바꾸지 않았다
- `cd app && uv run pytest`: 373 passed, 13 warnings
- 이후 `quiz generate` 배치에만 쓰인다. 고정 풀(`ps_326384fb5422`)과 `data/quiz.db`는 바꾸지 않았다
- Judge 프롬프트와 Judge 항목은 바꾸지 않았다. `packs/langchain/prompts/`에 `judge_items.json`이 없으므로 Judge 항목은 지금 4+2개 그대로다

### 6번: `data/quiz.db` 행 수 (2026-11-05 17:43, `mode=ro`)

0단계([01-harness.md](01-harness.md))와 13개 테이블 모두 같다. attempts 40, audit_records 20, audits 1, batch_slots 122, batches 15, grounding_records 212, pool_snapshot_items 122, pool_snapshots 3, questions 117, quiz_sets 9, review_items 21, schema_version 2, verification_results 209.

### 5번: design.md 개정 (2026-11-05 17:50)

- 차이를 보였다: 3.2 `QUIZ_PROMPTS_DIR`와 `judge_items.json`, 4.1 `experiments.py`·`data/experiments/`, 7.2 `generate --slots`·`experiment judge`·`experiment summary`·운영 DB 보호, 8.3 실험 Judge의 Langfuse 미기록, 9장 D-16. 사용자 답 "모두 반영"
- design.md 12.1 → 13.0. 10장 요구사항 7.3 행에 `experiment summary`를 더했다. Judge 항목과 실패 이유 목록은 바꾸지 않았다(EXP-1 보류)
- 모델 교체 제안: 없다. EXP-1에서 예비 모델(Haiku 4.5)은 교체 기준을 채우지 못했다. NFR-4 개정 안건은 없다

## 인계

갱신: 2026-11-05 17:36
- 마지막 완료 작업: 5단계 전체. 사용자 확인
- 다음 작업: `doc` 모드. 기록 파일 `06-output.md`, 최종 문서 `docs/04-prompt-model-experiments/output/experiments.md`. 장 구성을 먼저 확인받는다
- 실행 중: 없음
- 사용자 대기: 없음
- 먼저 읽을 파일: 이 파일 "1번"과 "결정", `exp-1.md`, `exp-2.md`, 계획 "5단계 뒤"

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| EXP-1 보류 | `arena` Judge 프롬프트와 `explanation_correct`를 반영하지 않는다. 고정 기준은 충족했지만 근거가 1문항이고, 대조군의 0은 문항 구성으로 정해졌고, 오탈락 문항이 실제 결함일 수 있다(누수 4, 2). 독립 라벨 데이터셋으로 다시 할 실험 후보로 남긴다 | 계획 1장 결정 6(Judge 항목 추가 허용)은 반영하지 않는다. design.md Judge 항목과 실패 이유는 바꾸지 않는다 |
| EXP-2 채택 | `arena` `generate.md`를 `packs/langchain/prompts/`에 반영한다. 이후 배치에만 쓴다 | 없음(결정 8) |

## 계획과 다른 점

- 없음

## 끝나는 조건 확인

- 조건: 누수 점검 결과와 채택 결정이 기록됐다. `data/quiz.db` 행 수가 0단계와 같다.
- 결과(2026-11-05 17:50): 충족. 누수 점검 결과는 "1번", 채택 결정은 "결정" 표에 있다(EXP-1 보류, EXP-2 채택). `data/quiz.db` 13개 테이블 행 수가 0단계와 같다
