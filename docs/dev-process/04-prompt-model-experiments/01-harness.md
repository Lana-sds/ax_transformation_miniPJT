# 01 하네스와 데이터셋 기록

상태: 완료
시작: 2026-11-05 16:10
완료: 2026-11-05 16:36 (사용자 확인 "완료")
계획: [04-prompt-model-experiments-plan.md](../04-prompt-model-experiments-plan.md)의 0, 1단계
세션 모델: Opus 5.5(`claude-opus-5-5`), 추론 강도 미확인(세션 설정 값을 이 세션에서 읽지 못했다)

## 입력

- 계획 결정 5, 6, 7
- `data/quiz.db`(읽기 전용), [06-m5.md](../03-implementation/06-m5.md) 감사 메모와 교차 풀이 검토

## 진행

### 0단계

- 2026-11-05 16:10 `cd app && uv run pytest`: 323 passed, 13 warnings.
- 2026-11-05 16:10 `data/quiz.db` 테이블별 행 수(읽기 전용 `mode=ro`로 셈). 5단계 끝에 다시 센다.

| 테이블 | 행 수 |
| --- | --- |
| attempts | 40 |
| audit_records | 20 |
| audits | 1 |
| batch_slots | 122 |
| batches | 15 |
| grounding_records | 212 |
| pool_snapshot_items | 122 |
| pool_snapshots | 3 |
| questions | 117 |
| quiz_sets | 9 |
| review_items | 21 |
| schema_version | 2 |
| verification_results | 209 |

- 커밋되지 않은 변경: 추적 파일 변경은 없다. 미추적 파일 `docs/concepts/guardrails-and-tracing.md`, `docs/concepts/reading-traces.md`는 이 단계와 무관한 사용자 파일이라 커밋하지 않았다. 워커 기준 커밋은 `dcb026325a3dde8ba9ad81e931c2b1cdf5ede43d`다.

### 1단계

- 2026-11-05 W1(1-가) 격리 worktree 워커를 띄웠다. 기준 `dcb026325a3dde8ba9ad81e931c2b1cdf5ede43d`.

#### 1-나 EXP-1 라벨 목록 초안 (2026-11-05, 사용자 확인 전)

출처: `audit_records`(`au_326384fb5422`) 메모 20행, `data/crosscheck/ps_5dac983c4b29.json` `reviewed`. 문항 ID 앞 `b20261105-`를 줄였다. "기대 항목"은 이 결함을 잡을 Judge 항목이다. 탐지는 Judge가 어떤 이유로든 탈락시키면 센다. 기대 항목 일치는 따로 센다.

실제 결함(18):

| 문항 | 형식 | 유형 | 근거(메모 요약) | 기대 항목 |
| --- | --- | --- | --- | --- |
| `03-010` | multi | 정답 키 | 교차 풀이 `key_error`. C 해설이 원문 표와 다르다 | `answer_key_correct` |
| `03-008` | short | 인용 무관 | 교차 풀이 `weak_grounding`. 인용이 `score_threshold`를 말하지 않는다. 전제가 실제 동작과 다르다 | `quote_supports_answer` |
| `03-009` | single | 해설 오류 | B 해설이 `rank_fusion` 실제 소스와 다르다 | `explanation_correct` |
| `03-021` | single | 해설 오류 | D 해설이 D가 아니라 A를 반박한다 | `explanation_correct` |
| `03-013` | single | 해설 오류 | C 해설 "하나의 경로만 선택"이 인용과 반대다 | `explanation_correct` |
| `01-002` | single | 해설 오류(약함) | 오답 해설이 부재 논증뿐이다. 정답 키와 인용은 맞다 | `explanation_correct` |
| `03-040` | short | 단서 | 지문이 정답 동작을 풀어 쓴다 | `no_cue`(대조군은 단답에 이 항목이 없다) |
| `05-007` | short | 단서 | 지문 코드에 정답 `operator.add`가 있다 | `no_cue`(같음) |
| `04-017` | short | 단서 | 지문이 함수 이름 `wait_for_all_tracers`를 풀어 쓴다 | `no_cue`(같음) |
| `01-001` | single | 단서 | 정답 보기 C가 인용 문장을 거의 그대로 옮겼다 | `no_cue` |
| `03-044` | code | 단서 | 지문 주석이 결함 위치를 가리킨다. 정답 A 문구가 문서 문장이다 | `no_cue` |
| `03-033` | short | 인용 무관 | 둘째 인용이 정답과 무관하다 | `quote_supports_answer` |
| `05-001` | code | 인용 무관 | 둘째 인용 "These methods"가 `retriever.invoke`를 말하지 않는다 | `quote_supports_answer` |
| `03-059` | single | 모호·전제 누락 | `pytest-recording` 전제가 빠졌다 | `answer_key_correct`, `distractors_wrong` |
| `03-056` | code | 모호·전제 누락 | 질문 두 개가 충돌한다. `ignore_llm` 인스턴스 설정은 `AttributeError`다 | `answer_key_correct` |
| `04-009` | code | 모호·설계 결함 | 가짜 모델이 순서대로 답해 스레드 격리를 검증하지 못한다. A 해설 인과가 틀렸다 | `answer_key_correct`, `explanation_correct` |
| `03-060` | short | 모호 | `pytest-vcr`도 답으로 주장될 수 있다 | `answer_key_correct` |
| `03-023` | multi | 매핑 불충실 | 감사 체크 `mapping_unfaithful=1`. "TWO를 고르라"가 번역에서 빠졌다 | `mapping_faithful` |

계획은 "약 17개"였다. `03-023`(매핑 불충실)을 더해 18개다.

정상 문항:

| 묶음 | 수 | 문항 | 기준 |
| --- | --- | --- | --- |
| `audit_clean` | 4 | `03-039`(single), `02-004`(code), `04-012`(short), `03-048`(multi) | 감사 메모가 표시 문제나 다듬기 권고뿐이다. `03-048`은 지문 표현·전제 보완 권고가 있다(경계) |
| `crosscheck_clean` | 32 | 현재 풀 `ps_326384fb5422` 중 감사 표본이 아니고, 교차 풀이에서 걸리지 않았고, 두 모델 모두 정답 키와 일치한 문항. single 9, multi 12, short 11 | `03-045`는 뺐다. T5.3 임시 DB 시험 감사에서 매핑 메모와 "해설이 인용 밖 내용을 든다" 관찰이 있었다 |

결함 주입 24는 `crosscheck_clean` 문항 사본으로 만든다. 원본 문항은 정상 묶음에도 그대로 남는다(짝 비교).

#### 사용자 확인 (2026-11-05, 결정 7)

| 질문 | 답 |
| --- | --- |
| 실제 결함 18개(`03-023` 포함)로 고정하는가 | 18개로 고정 |
| `01-002`(오답 해설이 부재 논증뿐)를 결함으로 세는가 | 해설 오류로 센다 |
| `03-048`을 `audit_clean`에 넣는가 | 정상에서 뺀다. 결함으로도 세지 않는다 |

고정한 라벨: 실제 결함 18개(위 표 그대로), `audit_clean` 3개(`03-039`, `02-004`, `04-012`), `crosscheck_clean` 32개. `03-048`, `03-045`는 EXP-1 문항에서 뺀다.

#### 1-나 EXP-2 슬롯 (2026-11-05)

- `data/experiments/EXP-2/build_slots.py`(시드 `20261105`)로 `data/experiments/EXP-2/slots.json`을 만들었다. 12슬롯, 버킷당 2, 형식 4종 3개씩. 같은 버킷 안 두 슬롯은 주제가 다르다.
- 뺀 주제: 페이지 경로에 `langsmith/studio` 또는 `graph-api-control-flow`가 든 주제. arena 과제 정의에 실패 예시로 보인 페이지다.
- 슬롯 항목은 `slots._slot` 출력 모양(버킷, 주제, 형식, 유형, 페이지 등)이다. W1 `--slots` 입력 모양과 맞는지는 W1 병합 뒤 확인한다.

| 버킷 | 형식 | 유형 | 주제 |
| --- | --- | --- | --- |
| rag | single | error_cause | Chroma |
| rag | multi | code_behavior | 청킹·메타데이터 |
| langgraph_basics | short | error_cause | ReAct |
| langgraph_basics | code | code_behavior | State·노드·엣지 |
| tool_mcp | single | error_cause | `@tool` |
| tool_mcp | multi | design | `langchain-mcp-adapters` |
| middleware_hitl_guardrails | single | code_behavior | 훅 호출 순서 |
| middleware_hitl_guardrails | multi | code_behavior | 로깅·마스킹·요약 미들웨어 |
| multi_agent | short | concept | 라우팅 검증 |
| multi_agent | code | code_behavior | 서브 Agent 설계 |
| ops_quality | short | error_cause | 통합 점검 |
| ops_quality | code | error_cause | Plan-and-Execute |

#### W1 병합

- W1 보고: 테스트를 먼저 써서 수집 실패(`quiz.experiments` 없음)를 본 뒤 구현했다. 워커 worktree 전체 테스트 355 passed(기존 323 + `test_experiments.py` 32). 새 worktree에는 `sandbox/.venv`가 없어 `test_sandbox_client.py` 6개가 처음에 실패했고, `uv sync --project sandbox --frozen`으로 풀렸다(저장소 변경 없음).
- `git merge-base --is-ancestor dcb0263 be9c639` 통과.
- 병합: W1 `worktree-agent-ac51c29fa8affbcb2` @ `be9c639ebf29dfb01774afef5a03dafc92b38d6e` → `308579ce986313d9edc7300afbee8ec7f0c29df5`
- 병합 뒤 이 worktree `cd app && uv run pytest`: 355 passed, 13 warnings.
- 바뀐 파일: `app/quiz/pipeline/prompts.py`, `app/quiz/pipeline/nodes.py`, `app/quiz/pipeline/schemas.py`, `app/quiz/batch.py`(`fixed_slots` 인자), `app/quiz/cli.py`, 새 `app/quiz/experiments.py`, 새 `app/tests/test_experiments.py`. 새 의존성 없음.

#### 1-나 EXP-1 `items.json`

- `data/experiments/EXP-1/build_items.py`(시드 `20261105`)로 `data/experiments/EXP-1/items.json`을 만들었다. sha256 `0a0a4f1c410864877c8b0bbcd4b651fd1f22cab38595d190a3f8c79d96f0ff7a`.
- 77문항: 실제 결함 18, `audit_clean` 3, `crosscheck_clean` 32, 결함 주입 24. 형식 multi 25, short 24, single 23, code 5.
- 결함 주입(원본은 `crosscheck_clean`, 원본 24개가 서로 다르다):

| 유형 | 원본 형식 | 수 | 만드는 법 | 기대 항목 |
| --- | --- | --- | --- | --- |
| `key_error` | single, multi | 6 | 정답 키 하나를 오답 보기 하나로 바꾼다. 해설은 그대로 | `answer_key_correct` |
| `explanation_error` | single, multi | 6 | 오답 보기 하나의 해설 본문을 다른 보기의 해설 본문으로 바꾼다 | `explanation_correct` |
| `cue` | single, multi | 6 | 오답마다 " This always happens."를 붙이고, 정답 보기에 군더더기 문장을 붙여 가장 긴 오답의 1.6배 넘게 늘린다(정답 42~51단어, 가장 긴 오답 18~28단어) | `no_cue` |
| `quote_irrelevant` | short | 6 | 인용을 모두 같은 페이지의 무관한 평문 문장(정답 문자열이 없고 원래 인용에서 1500자 넘게 떨어진 곳)으로 바꾼다 | `quote_supports_answer` |

- 계획은 "`quote`를 무관한 문장으로 바꿈"이었다. 인용이 둘 이상인 문항은 하나만 바꾸면 남은 인용이 정답을 받쳐 라벨이 모호해진다. 그래서 모두 바꿨다.
- 해설 문단 머리(`**A (정답):**`, `A. 정답입니다`, `A선택지:` 등)를 파싱하지 못한 문항은 `explanation_error` 원본에서 뺐다.
- 건조 실행: `experiments._prepare`로 77문항의 Judge 입력을 만들었다. 오류 0. 문항당 근거 페이지 원문 평균 80,913자.

#### 비용 예비 추정 (모델 호출 없음)

- 문항당 입력 약 2만 토큰(원문 80,913자를 4자당 1토큰으로 셈. 실제 토크나이저 값은 미확인)이다.
- Sonnet 4.5 실행 3회(`control` 2회, `arena` 1회) × 77 = 231호출, 입력 약 510만 토큰, 약 15 USD. 출력은 호출당 500토큰으로 잡으면 약 1.7 USD.
- Haiku 4.5 실행 2회 × 77 = 154호출, 입력 약 340만 토큰. `data/pricing/bedrock.yaml`에 `global.anthropic.claude-haiku-4-5-20251001-v1:0` 행이 없다. 단가는 미확인이다. 행이 없으면 하네스가 비용을 `None`으로 적는다. 3단계 전에 AWS Price List로 단가를 확인해 행을 더해야 한다. 입력 1 USD/1M으로 가정하면 약 3.4 USD다.
- EXP-1 합 약 20 USD(Haiku 가정 포함). 계획 추정(5~10 USD)의 두 배다. EXP-2 추정(7~14 USD)을 더하면 상한 30 USD를 넘을 수 있다. 3단계 2번(첫 실행 뒤 실제 단가로 재추정)에서 다시 판단한다.

## 인계

갱신: 2026-11-05 16:36
- 마지막 완료 작업: W1 병합, EXP-1 `items.json`, 2단계 F
- 다음 작업: 3단계(EXP-1 실행). 시작 전에 아래 사용자 대기 3건을 닫는다
- 실행 중: 없음
- 사용자 대기: (1) EXP-1 비용 예비 추정 약 20 USD. 계획대로 첫 실행 뒤 재추정할지, 실행 수·문항 수를 줄일지 (2) `data/pricing/bedrock.yaml`에 Haiku 4.5 행 추가(단가 미확인, AWS Price List로 확인) (3) `quiz experiment judge`의 `.env` 읽기 허용과 CLAUDE.md 한 줄 추가
- 먼저 읽을 파일: 이 파일 "비용 예비 추정", 계획 3장 3단계

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 프롬프트 디렉토리 | `QUIZ_PROMPTS_DIR`를 호출할 때마다 읽는다. 없으면 `packs/langchain/prompts/`다. 상대 경로는 현재 디렉토리 기준이다 | design.md에 없음(결정 5). 승인 뒤 반영 |
| Judge 항목 확장 | 프롬프트 디렉토리의 `judge_items.json`(`extra_items[]`: `name`, `description`, `formats`). 없으면 지금 4+2개 그대로. 거짓이면 `judge_fail:<name>` | design.md에 없음(결정 5, 6) |
| 고정 슬롯 | `quiz generate --slots <json>`. 각 슬롯은 `slot_for`로 다시 만든다. `--count N`은 앞 N개만 쓴다 | design.md에 없음(결정 5) |
| 실험 명령 | `quiz experiment judge --items --arm [--model] [--exp]`, `quiz experiment summary --exp [--compare a,b]` | design.md에 없음(결정 5) |
| 운영 DB 보호 | `--slots`나 `QUIZ_PROMPTS_DIR`를 쓰면서 DB가 `data/quiz.db`면 `quiz generate`가 거부한다(종료 코드 1) | 없음 |
| `experiment judge`의 `.env` | Bedrock을 부르므로 `.env`를 읽는다 | CLAUDE.md "`.env`는 `generate`, `crosscheck` CLI만 읽는다"와 다르다. 사용자 승인 뒤 CLAUDE.md를 고친다 |
| 실험 Judge의 범위 | Judge 노드만 돈다. 코드형 문항의 샌드박스 실행 대조(`judge_exec_mismatch`)는 하지 않는다. Langfuse trace를 남기지 않는다 | 없음. 보고서 "타당성 위협"에 적는다 |
| 결함 주입 인용 | 인용을 모두 바꾼다 | 계획 1-나 5번 문구 |
## 계획과 다른 점

- 1-나 1번(`.gitignore`에 `data/experiments/**/*.db` 추가)은 하지 않는다. 기존 `.gitignore`의 `*.db` 줄이 이미 덮는다.
- 1-나 7번 "실패 사례가 있던 주제와 겹치지 않게"를 "변형 작성자에게 실패 예시로 보인 페이지의 주제를 뺀다"로 해석했다. `quote_mismatch`가 한 번이라도 난 주제를 모두 빼면 측정할 신호가 줄어든다.
- 1-나 5번 결함 주입 문항과 6번 `items.json`은 W1이 정한 입력 모양(인라인 문항)을 보고 만든다. W1 병합 뒤로 미룬다.

## 끝나는 조건 확인

- 조건: 병합 뒤 `uv run pytest` 통과. 가짜 모델로 `quiz experiment summary`가 표를 낸다. EXP-1 라벨 목록을 사용자가 확인했다.
- 결과(2026-11-05 16:35): 충족.
  - 병합 뒤 `uv run pytest` 355 passed.
  - 가짜 모델 summary: `test_summary_exp1_tables_have_columns`, `test_summary_exp2_reuses_metrics_and_has_columns` 통과. 실제 `data/experiments/EXP-1`에는 arm 결과가 아직 없어 `quiz experiment summary --exp EXP-1`이 "no arm results"를 낸다(정상).
  - EXP-1 라벨 목록: 사용자가 2026-11-05에 확인했다(위 "사용자 확인").
