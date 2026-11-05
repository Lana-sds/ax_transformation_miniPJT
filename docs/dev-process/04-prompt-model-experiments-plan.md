# 04 프롬프트와 모델 실험 단계 실행 계획

상태: 초안
작성일: 2026-11-05
수정: 2026-11-05, 결정 1을 "준비 작업(1, 2단계)은 지금 03과 병행"으로 닫았다(사용자 선택). 04 전용 worktree `C:/Users/SDS/orca/workspaces/ax_transformation/04-prompt-model-experiments`(브랜치 `Lana-sds/04-prompt-model-experiments`, 기준 `Lana-sds/03-implementation`)를 만들었다. 이 단계의 코디네이터는 그 worktree의 세션이다. 결정 7(Bedrock 실행 위치)을 더했다
대상: [input/README.md](../04-prompt-model-experiments/input/README.md)에 링크한 입력 7개. 03 단계는 진행 중이다(M5~M7 남음)
근거: [skillset-by-lifecycle.md](skillset-by-lifecycle.md)의 "4. 프롬프트와 모델 실험" 행. 도구 설명은 pstack(README, `skills/arena/SKILL.md`)과 ouroboros README를 2026-11-05에 다시 확인했다.

## 1. 목표

- **입력**: [input/README.md](../04-prompt-model-experiments/input/README.md). 요구사항 NFR-4·NFR-5·7.3, 설계서, 03 기록의 파일럿 숫자, `packs/langchain/prompts/`, `data/quiz.db`, `data/crosscheck/`
- **산출물**:
  - 코드: 실험 하네스(1단계). `docs/` 밖에 둔다.
  - 실험 자료: `data/experiments/<EXP-n>/`. 변형 프롬프트, 슬롯·문항 목록, 결과 JSON, 실험 DB(`*.db`는 git 제외)
  - `docs/04-prompt-model-experiments/output/`: 실험별 결과 요약
- **최종 문서**: `docs/04-prompt-model-experiments/output/experiments.md`. 실험 보고서(`.claude/skills/stage/templates/output-types.md`의 04 행, 초기안). `doc` 모드에서 장 구성을 사용자와 확인한다.
- **부산물**: 도구별 사용 기록과 평가. `docs/dev-process/04-prompt-model-experiments/`에 둔다.
- **닫아야 할 결정**:
  1. 시작 시점: **1, 2단계는 지금 03과 병행한다(2026-11-05, 사용자 선택)**. Bedrock 호출(3, 4단계)은 03의 Bedrock 작업(T5.6 재채움이 필요하면 그것까지)이 끝난 뒤에 한다. 실험은 Bedrock 일일 토큰 한도를 03과 나눠 쓰기 때문이다.
  2. 실험 범위. 추천: EXP-1, EXP-2만 한다. EXP-3, EXP-4는 후보로 남긴다(2장 "실험 후보").
  3. pstack `/arena` 설치 여부. 추천: 설치하지 않고 방법만 빌린다. 01 단계 gstack `/office-hours`와 같은 방식이다. 이유는 4장 위험 표에 있다.
  4. 비용 상한. NFR-4.4는 상한을 정하지 않았다. 추천: 이 단계 합계 25 USD. 넘으면 멈추고 묻는다.
  5. 하네스 위치와 인터페이스. design.md 4.1과 6장(인터페이스)에 없는 요소다. 추천안은 1단계에 있다. 정한 값은 기록 파일 "결정" 표에 적고, design.md는 사용자 승인 뒤 고친다.
  6. 채택 반영 범위. 추천: 채택한 프롬프트는 `packs/langchain/prompts/`에 반영하되 이후 배치에만 쓴다. 고정 풀(`ps_326384fb5422`)은 다시 만들지 않는다. 모델 교체는 NFR-4 개정이 필요하므로 이 단계에서는 제안만 한다.
  7. Bedrock 실행 위치. 04 worktree에는 `.env`와 `data/quiz.db`가 없다(git 제외). CLAUDE.md는 Bedrock 호출과 `.env`가 필요한 작업을 03 worktree에서만 돌리게 한다. 1, 2단계는 둘 다 필요 없다. 실패 사례 원문은 `QUIZ_DB`로 03의 `data/quiz.db`를 읽기 전용으로 읽는다. 3, 4단계 전에 정한다. 후보: (가) 04 브랜치를 03 worktree에 병합하고 거기서 실행한다. (나) 사용자가 `.env`를 04 worktree에 직접 복사하고 CLAUDE.md 규칙을 고친다.

## 2. 도구별 역할

| 도구 | 역할 | 입력 | 출력 | 이 환경 상태 |
| --- | --- | --- | --- | --- |
| pstack `/arena` (방법만 차용, 결정 3) | 1순위. 같은 과제를 후보 N개가 병렬로 시도하고, 하나를 기반으로 골라 나머지의 좋은 부분을 옮긴다. 변형 프롬프트를 만든다 | 대조군 프롬프트, 기준선 실패 이유, 채점 기준 | 실험별 변형 1개, 합성 노트 | 미설치(`~/.claude/plugins/installed_plugins.json`에 없음, 2026-11-05) |
| paperthin `mandela` | 실험 설계와 결과의 평가 누수를 점검한다. 04 보고서의 "타당성 위협" 장 재료 | 실험 설계, 데이터셋 구성, 결과 | 해당하는 누수 유형과 독립성 보완안 | 설치됨(세션 스킬 목록, `~/.agents/skills/mandela`, 2026-11-05) |
| paperthin `readchk` | 단계 시작 지시를 맞게 읽었는지 검증한다 | 단계 지시 | 갈림길이 남을 때만 질문 | 설치됨(세션 스킬 목록, 2026-11-05) |

제품이 쓰는 기술(도구 선택 대상 아님):

- Bedrock(NFR-2, NFR-4): 실험 호출. 단가는 `data/pricing/bedrock.yaml`을 쓴다.
- Langfuse(NFR-5): 실험 배치도 `batch_id` 태그로 trace가 남는다. 꺼도 돈다(NFR-5.4).

고르지 않은 도구:

- ouroboros `evolve`: 보조 도구다. MCP는 연결된다(`ouroboros_project_status` 응답, 2026-11-05). 뺀 이유: README는 `evolve`가 Seed 온톨로지를 세대마다 바꾼다고 설명한다. 프롬프트를 바꾼다는 설명은 없다. 실행도 ouroboros 자체 파이프라인으로 하므로 이 앱의 생성·Judge 파이프라인을 측정하지 않는다. "이 프로젝트의 선택" 절의 계획 도구 하나 규칙에도 걸린다.
- gstack, gajae-code: "이 프로젝트의 선택" 절이 제외했다.
- paperthin `re0-plan`, `re0-loop`: "이 프로젝트의 선택" 절이 계획 도구와 겹친다고 제외했다.

도구 설명 요약:

- pstack `/arena`(`skills/arena/SKILL.md`, 2026-11-05):
  - 입력은 과제, 공유 근거 경로, 채점 기준 3~6개다. 후보는 모두 같은 프롬프트를 받는다. 후보는 과제만 보고 채점 기준은 보지 않는다.
  - 후보는 백그라운드 서브에이전트로 한 메시지에서 띄운다. 출력은 후보마다 worktree나 별도 디렉토리에 둔다.
  - 다른 모델 계열의 읽기 전용 교차 Judge가 채점 기준별로 점수를 매긴다. 다른 계열을 못 쓰면 교차 Judge를 건너뛰고 그렇다고 적는다.
  - 기반 하나를 고르고, 나머지 후보에서 한두 가지를 손으로 옮긴다. 후보가 크게 갈리면 과제 정의가 부족하다고 보고 다시 정의해 다시 돌린다.
  - 결과는 합성 산출물 하나와 합성 노트(기반과 이유, 교차 Judge 결과, 옮긴 것과 출처, 버린 것과 이유, 검증 결과)다.
  - 설정 경로(`~/.cursor/rules/pstack-models.mdc`)와 모델 이름은 Cursor 기준이다. 절차 자체는 Cursor에 묶이지 않는다고 적혀 있다.
- ouroboros `evolve`(README, 2026-11-05): 평가 출력이 다음 세대 Seed의 입력이 된다. 온톨로지 유사도 0.95 이상에서 수렴한다. 최대 30세대다.
- `mandela`(스킬 설명, 2026-11-05): 외부 정답이 독립적으로 들어오는지, 모델·채점자·설계자가 같은 결과를 서로 확인만 하는지 본다. 누수 유형 8개 중 해당하는 것만 내고 읽기 전용이다.

### 기준선

`data/quiz.db`를 읽기 전용으로 집계했다(2026-11-05). 03 T6.1의 `data/metrics/baseline.json`이 생기면 그 값을 기준으로 바꾼다.

| 지표 | 값 |
| --- | --- |
| 문제 상태 | passed 60, dropped 55, audit_failed 2 |
| 버린 이유 | duplicate 27, regen_exhausted 17, version_conflict 11 |
| 검증 시도 | 209 |
| 시도별 `quote_match` | 93/209 |
| 시도별 `judge_pass` | 204/209 |
| 실패 이유 출현 수 | quote_mismatch 157, duplicate 27, version_conflict 11, judge_exec_mismatch 10, judge_fail:answer_key_correct 1, mapping_missing 1 |
| 형식별 passed/생성 | single 18/27, multi 14/27, short 17/27, code 11/36 |
| 배치 비용 | 15개 배치 합 36.75 USD |

### 실험

| ID | 질문 | 가설 | 관련 요구 ID |
| --- | --- | --- | --- |
| EXP-1 | 생성 프롬프트 변형이 인용 복사 실패를 줄이는가 | 변형은 첫 시도 `quote_match` 비율을 올리고 passed당 비용을 낮춘다 | FR-8.3, NFR-4.4, 7.3 |
| EXP-2 | Judge가 결함 있는 문제를 떨어뜨리는가 | 지금 Judge는 정답 키 결함을 일부 놓친다. 변형 Judge 프롬프트는 검출률을 올린다. 예비 모델(NFR-4.3)은 더 싸지만 검출률이 낮다 | NFR-4.2, NFR-4.3, 7.2 |

실험 후보(결정 2에서 넣으면 같은 방식으로 단계를 더한다):

| ID | 질문 | 근거 숫자 |
| --- | --- | --- |
| EXP-3 | 코드형 생성 프롬프트 변형이 코드형 수율을 올리는가 | code passed 11/36, judge_exec_mismatch 10 |
| EXP-4 | 같은 버킷의 기존 문제 요약을 생성 프롬프트에 주면 중복 탈락이 줄어드는가 | duplicate 27 |

## 3. 진행 순서

### 0단계: 사전 준비

1. 1장 결정 1~6을 닫는다.
2. 선행 확인: 03 T6.1(`quiz metrics`)이 병합되어 있다. 하네스가 이 집계 함수를 다시 쓴다.
3. Bedrock 호출 전 확인: 03의 Bedrock 작업이 끝났다(결정 1). `.env`와 `AWS_REGION`이 있다.
4. 기록 파일마다 시작·완료 시각을 남긴다.

### 1단계: 실험 하네스

- 입력: 결정 5, 03 T6.1 집계 함수
- 하는 일(추천안. 결정 5에서 바꿀 수 있다):
  - 프롬프트 디렉토리를 환경 변수 `QUIZ_PROMPTS_DIR`로 바꿀 수 있게 한다. 없으면 지금 경로(`packs/langchain/prompts/`)다.
  - 실험 DB는 기존 `QUIZ_DB`로 `data/experiments/<EXP-n>/<arm>.db`를 가리킨다. `data/quiz.db`에는 쓰지 않는다.
  - `quiz generate`에 고정 슬롯 목록 입력(`--slots <json>`)을 더한다. 같은 슬롯을 대조군과 변형에 똑같이 준다.
  - `quiz experiment judge --items <json> --arm <이름> [--model <id>]`: 생성 없이 Judge 노드만 돌려 문항별 판정을 `data/experiments/EXP-2/<arm>.json`에 쓴다.
  - `quiz experiment summary --exp <EXP-n>`: arm마다 T6.1 집계와 EXP별 지표를 표로 낸다.
  - 테스트를 먼저 쓴다. 가짜 모델로 (1) 프롬프트 경로 바꿈, (2) 실험 실행 뒤 `data/quiz.db` 행 수가 그대로임, (3) summary 표의 열을 확인한다.
- 끝나는 조건: `uv run pytest` 통과. 가짜 모델로 `quiz experiment summary`가 표를 낸다.
- 기록 파일: `01-harness.md`

### 2단계: arena 방법으로 변형 만들기

- 입력: 대조군 프롬프트(`generate.md`, `formats/*.md`, `judge.md`, `judge/*.md`), 기준선 실패 이유, 실패 사례 원문(`verification_results.fail_reasons_json`, `judge_verdict_json`)
- 하는 일: 실험마다 한 번 arena 절차를 따른다.
  1. 과제 정의: 과제와 공유 근거 경로를 쓴다. 채점 기준은 3~6개다. 공통 기준: 출력 스키마를 바꾸지 않는다. T2.11 품질 규칙 문구를 유지한다. 정답 키, 허용 답안, 매핑 규칙(CLAUDE.md 고정 결정)을 지킨다. 길이는 대조군의 1.3배 이하다. EXP-1 기준: 인용 복사 지시. EXP-2 기준: 결함 유형(정답 키 오류, 인용 불일치)을 찾는 지시.
  2. 후보 2개를 백그라운드 서브에이전트로 한 메시지에서 띄운다. 후보 출력은 `data/experiments/<EXP-n>/arena/candidate-<k>/`에 둔다.
  3. 교차 Judge: 서브에이전트는 Claude 계열만 쓸 수 있다. 다른 계열 교차 Judge는 건너뛰고 기록한다(SKILL.md 규칙).
  4. 기반을 고르고 옮길 것을 손으로 합친다. 결과를 `data/experiments/<EXP-n>/variants/arena/`에 둔다. 대조군은 `variants/control/`에 복사한다.
  5. 검증: 1단계 테스트를 변형 디렉토리로 다시 돌린다. 프롬프트 문구 테스트(T2.11 확인 (1))가 통과해야 한다.
- 끝나는 조건: 실험마다 `variants/control/`, `variants/arena/`와 합성 노트가 있다. 프롬프트 문구 테스트가 변형에서도 통과한다.
- 기록 파일: `02-arena.md`

### 3단계: EXP-1 실행

- 고정 조건: 생성 모델 NFR-4.1, Judge 모델 NFR-4.2, 같은 슬롯 목록, 같은 스냅샷(`packs/langchain/snapshots/` sha256), 재생성 한도는 지금 값
- 데이터셋: 12슬롯(버킷당 2, 형식 4종이 각각 3개). 슬롯 목록은 `data/experiments/EXP-1/slots.json`에 고정한다.
- arm: `control`, `arena`. 같은 슬롯을 두 arm에 돌린다.
- 지표: 첫 시도 `quote_match` 비율, passed 수, 버린 이유, 시도당 Judge 통과율, T2.11 실패 수, passed당 비용, 걸린 시간
- 판정 기준(실행 전에 고정): `arena`가 첫 시도 `quote_match` 비율이 더 높고, passed 수가 같거나 많고, passed당 비용이 같거나 낮으면 채택 후보다. Judge 통과율이나 T2.11 실패가 대조군보다 나빠지면 기각한다.
- 끝나는 조건: 두 arm의 summary 표가 `docs/04-prompt-model-experiments/output/exp-1.md`에 있다. 판정이 기록됐다.
- 기록 파일: `03-exp1.md`

### 4단계: EXP-2 실행

- 고정 조건: 같은 문항 목록, `temperature=0`(지금 Judge 설정)
- 데이터셋(`data/experiments/EXP-2/items.json`):
  - 정상 24: 고정 풀에서 버킷당 4개를 무작위로 뽑는다. 시드를 기록한다.
  - 결함 주입 24: 정상 24의 사본에 결함 하나씩을 넣는다. 12개는 정답 키를 오답 보기로 바꾸고, 12개는 `quote`를 같은 스냅샷의 무관한 문장으로 바꾼다. 결함은 구성으로 정해지므로 정답 라벨이 Judge와 독립이다.
  - 실제 결함 2: `audit_failed` 2문항(06-m5.md)
- arm: Judge 프롬프트(`control`, `arena`) × 모델(NFR-4.2, NFR-4.3) = 4개
- 지표: 결함 유형별 검출률, 정상 문항 오탈락 수, 호출당 비용, 호출당 지연
- 판정 기준(실행 전에 고정): 프롬프트는 `arena`가 결함 검출률이 더 높고 정상 오탈락이 2개 이하면 채택 후보다. 예비 모델은 검출률이 NFR-4.2와 같거나 높을 때만 교체 제안을 기록한다(결정 6).
- 끝나는 조건: 네 arm의 표가 `docs/04-prompt-model-experiments/output/exp-2.md`에 있다. 판정이 기록됐다.
- 기록 파일: `04-exp2.md`

### 5단계: mandela로 누수 점검과 결정

- 입력: 3, 4단계의 설계, 데이터셋 구성, 결과
- 하는 일: `mandela`를 실행해 해당하는 누수 유형을 받는다. 결과를 "타당성 위협" 재료로 기록한다. 이미 아는 위협: EXP-2 정상 24는 같은 Judge(NFR-4.2, control)가 통과시킨 문항이라 그 arm의 오탈락이 낮게 나온다. 결함 판정이 바뀌면 사용자에게 보인다.
- 채택: 채택 후보를 사용자에게 보이고 승인받는다. 승인되면 `packs/langchain/prompts/`에 반영하고 기록 파일 "결정" 표에 적는다. 모델 교체 제안은 요구사항 NFR-4 개정 안건으로만 기록한다.
- 끝나는 조건: 누수 점검 결과와 채택 결정이 기록됐다.
- 기록 파일: `05-mandela.md`

### 병렬 실행

코디네이터는 04 worktree(`C:/Users/SDS/orca/workspaces/ax_transformation/04-prompt-model-experiments`)의 세션이다. 3, 4단계 실행 위치는 결정 7을 따른다. 03 T6.1은 03 브랜치에서 병합되면 04 브랜치로 `git merge Lana-sds/03-implementation`으로 가져온다. 워커 절차는 stage 스킬 run 3번을 따른다. 2단계 arena 후보 서브에이전트는 arena 절차의 일부이고 이 표의 워커가 아니다.

| 단계 | 줄 | 작업 | 소유 파일 | 선행 | 실행 위치 |
| --- | --- | --- | --- | --- | --- |
| 1, 2 | 코디네이터 | 2단계 arena 변형 | `data/experiments/*/arena/`, `data/experiments/*/variants/` | - | 04 worktree |
| 1, 2 | W1 | 1단계 하네스 | `app/quiz/pipeline/prompts.py`, `app/quiz/cli.py`, 새 `app/quiz/experiments.py`, `app/tests/test_experiments.py` | 03 T6.1 병합 | 격리 worktree |
| 2 | 코디네이터 | 2단계 5번 변형 검증 | - | W1 병합 | 04 worktree |
| 3, 4 | 코디네이터 | EXP-1 → EXP-2 | `data/experiments/` | 2단계, 결정 1 | 결정 7(Bedrock). 일일 토큰 한도 때문에 순서대로 한다 |
| 5 | 코디네이터 | 누수 점검과 채택 | `packs/langchain/prompts/`(승인 뒤) | 3, 4단계 | 04 worktree |

## 4. 사전 조건과 위험

| 항목 | 내용 | 대응 |
| --- | --- | --- |
| 03 미완료와 마감 | 03 마감은 2026-11-06 17:00이다. M5~M7이 남았다. 실험 호출은 Bedrock 일일 토큰 한도를 03과 나눠 쓴다 | 결정 1. Bedrock 호출은 03 Bedrock 작업 뒤에 한다 |
| 일일 토큰 한도 | 파일럿에서 us-east-1 두 프로필이 `ThrottlingException`("Too many tokens per day")에 걸렸다(04-m3.md) | 리전 전환(`llm.failover_chain`)을 그대로 쓴다. 그래도 걸리면 멈추고 `--resume`으로 다음 날 잇는다 |
| pstack 설치 영향 | 설치 명령은 `/plugin marketplace add cursor/plugins`, `/plugin install pstack@cursor-plugins`다. 서드파티 마켓플레이스는 자동 업데이트가 꺼져 있다. `/pstack:setup-pstack`은 `~/.claude/rules/pstack-models.md`를 쓴다. 훅과 전역 등록은 README에 없다(미확인). 설정과 모델 이름은 Cursor 기준이다 | 결정 3. 추천은 설치하지 않고 SKILL.md 절차만 따르는 것이다. 설치하면 이 계획 상단에 "수정:" 줄을 남긴다 |
| 교차 Judge 계열 | arena는 부모와 다른 계열의 교차 Judge를 쓴다. 서브에이전트는 Claude 계열만 쓸 수 있다 | 교차 Judge를 건너뛰고 기록한다. 변형의 실제 판정은 3, 4단계 측정으로 한다 |
| 표본 크기 | EXP-1 12슬롯, EXP-2 50문항이다. 차이가 작으면 우연과 구별하지 못한다 | 판정 기준을 실행 전에 고정한다. 결과는 "방향"으로만 쓰고 보고서 "타당성 위협"에 적는다 |
| 평가 누수 | EXP-2 정상 문항은 control Judge가 이미 통과시킨 문항이다. 변형 프롬프트를 만든 후보가 실패 사례를 보면 그 사례에 맞춘다 | 결함 라벨은 구성으로 정한다. EXP-1 슬롯은 기존 실패 사례와 다른 슬롯으로 뽑는다. 5단계 `mandela` |
| 운영 DB 오염 | 실험이 `data/quiz.db`나 고정 풀에 쓰면 03 결과가 바뀐다 | 실험마다 `QUIZ_DB`를 따로 둔다. 1단계 테스트 (2)로 확인한다. 실행 전후 `data/quiz.db` 행 수를 기록한다 |
| 모델 교체 | NFR-4가 모델을 정했다 | 측정만 한다. 교체는 요구사항 개정 승인 뒤의 일이다(결정 6) |
| 비용 | 추정: EXP-1 약 7~14 USD(파일럿 슬롯당 0.286 USD × 24슬롯, 재생성 포함 상한), EXP-2 약 5~10 USD(Judge 호출 200회). Judge 호출당 토큰은 미확인이다 | 결정 4. 3단계 첫 2슬롯 뒤 실제 단가로 다시 계산하고 기록한다. 상한을 넘을 것 같으면 멈추고 묻는다 |
| Langfuse 한도 | Hobby 월 5만 units다. 실험 호출 1회당 소모량은 미확인이다 | 실험 배치 뒤 사용량 화면을 확인하고 기록한다. 부족하면 Langfuse를 끄고 돌린다(NFR-5.4) |
| 하네스 설계 차이 | `QUIZ_PROMPTS_DIR`, `--slots`, `quiz experiment`, `data/experiments/`는 design.md에 없다 | 결정 5. 기록 파일 "결정" 표에 적고, design.md는 차이를 보인 뒤 승인받아 고친다 |

## 5. 기록과 평가

기록 위치는 `docs/dev-process/04-prompt-model-experiments/`이다.

| 파일 | 내용 |
| --- | --- |
| `01-harness.md` | 하네스 결정, 테스트 결과 |
| `02-arena.md` | 실험별 과제 정의, 후보, 교차 Judge 생략, 합성 노트 |
| `03-exp1.md` | EXP-1 실행 기록, 비용, 판정 |
| `04-exp2.md` | EXP-2 데이터셋 시드, 실행 기록, 판정 |
| `05-mandela.md` | 누수 점검 결과, 채택 결정 |
| `0N-retro.md` | 도구별 평가 |

평가 기준은 `.claude/skills/stage/templates/retro.md`를 따른다. 이 단계에서 추가하는 기준:

- arena 방법 차용이 변형을 하나 만들 때 대조군 대비 측정 차이를 냈는지
- 실험 비용 추정과 실제 비용의 차이
- `mandela`가 계획에서 미리 적은 위협 밖의 누수를 찾았는지
