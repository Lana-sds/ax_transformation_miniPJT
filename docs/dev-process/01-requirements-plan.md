# 01 요구사항 단계 실행 계획

작성일: 2026-11-04
수정: 2026-11-04, gstack을 설치하지 않고 `/office-hours`의 방법만 빌려 쓰기로 변경
대상: `docs/01-requirements/input/`의 문서 5개
근거: [skillset-by-lifecycle.md](skillset-by-lifecycle.md)의 "1. 아이디어와 요구사항" 행. 도구 설명은 각 저장소 README를 2026-11-04에 다시 확인했다.

## 1. 목표

- **입력**: `candidate_ccaf.md`, `candidate_langchain.md`, `design-option-a-docs-mcp-grounding.md`, `design-option-b-layered-openwiki.md`, `tech-stack-common.md`
- **산출물**: `docs/01-requirements/output/requirements.md` 하나. 구성은 목표와 범위, 기능 요구사항, 근거·검증 요구사항, 비기능 요구사항, 품질 지표, 미결 사항이다.
- **부산물**: 도구별 사용 기록과 평가. `docs/dev-process/01-requirements/`에 둔다.
- **닫아야 할 결정**:
  - 후보 선택(CCA-F 또는 LangChain)
  - 도메인 비중(LangChain 후보)
  - 시험 날짜(CCA-F 후보)
  - 웹앱 형태
  - 코드형 문제의 실행 환경
  - MVP 근거 자료 범위

## 2. 도구별 역할

| 도구 | 역할 | 입력 | 출력 | 이 환경 상태 |
| --- | --- | --- | --- | --- |
| paperthin `aim` | 문서 묶음을 읽고 "무엇을 하려는지"를 제안한다 | 문서 5개 | 확인할 의도 제안 1개 | 설치됨 |
| gstack `/office-hours` (방법만 차용) | 전제를 공격하고 대안을 낸다. 후보 선택에 쓴다 | `aim`이 확인한 의도, 두 후보 문서 | 설계 문서 | 설치하지 않음. 저장소를 읽기 전용으로 받아 섹션 문서만 참고 |
| ouroboros `interview` | 남은 모호성을 질문으로 닫고, 모호성 점수로 끝낼 시점을 정한다 | `/office-hours` 결과, 선택된 후보 문서 | 확정된 답, 모호성 점수 | 설치됨. 이 세션에서 MCP 연결 실패 |
| paperthin `readchk` | 내 지시를 모델이 맞게 읽었는지 검증한다 | 각 지시 | 보통 출력 없음. 갈림길이 남을 때만 질문 | 설치됨 |

도구 설명 요약:

- `aim`: 넘겨받은 데이터를 읽고, 의도를 묻는 대신 제안해서 확인받는다.
- `/office-hours`: 코드 작성 전에 문제를 먼저 이해시키는 스킬이다. 프레이밍에 반박하고, 전제를 공격하고, 구현 대안을 낸다. 결과는 다른 gstack 스킬이 읽는 설계 문서다.
  - 모드가 둘이다. 창업자용 startup mode(Phase 2A)는 질문 6개로 진단하고, builder mode(Phase 2B)는 설계 파트너 역할을 한다. 이 과제는 개인 학습 앱이라 builder mode에 가깝다.
  - 이번에 빌려 쓰는 부분은 Phase 2B(builder mode), Phase 3(전제 공격), Phase 4(대안 생성)이다.
- `interview`: 모호성을 `1 - Σ(clarity × weight)`로 계산한다. 0.2 이하가 되어야 Seed 생성으로 넘어간다.
- `readchk`: 지시를 속으로 다시 풀어 맥락과 대조한다. 풀리면 조용히 진행하고, 실제 갈림길이 남을 때만 묻는다.

## 3. 진행 순서

### 0단계: 사전 준비

1. ouroboros MCP 연결을 복구한다. 이 세션에서는 "recent failure cached" 상태로 연결이 건너뛰어졌다. 15분 뒤 자동으로 재시도되며, 바로 다시 시도하려면 플러그인 설정을 확인한다.
2. gstack 저장소를 scratchpad에 `git clone --depth 1 https://github.com/garrytan/gstack.git`로 받는다. `./setup`은 실행하지 않고, `~/.claude/skills/` 아래에도 두지 않는다. 받은 커밋 해시를 기록한다.
3. `office-hours/SKILL.md`와 2단계에 쓸 섹션 문서(`office-hours/sections/` 중 builder mode, 전제 공격, 대안 생성 해당 파일)를 읽는다.

### 1단계: `aim`으로 의도 확인

- 문서 5개를 넘기고 지시는 최소로 한다. 예: "이 문서들 봐줘"
- 기대하는 제안은 "후보 하나를 골라 `requirements.md`로 묶는다"이다.
- 제안이 기대와 다르면 그 차이를 기록한다. 내가 놓친 의도일 수 있다.

### 2단계: `/office-hours` 방법으로 발산

- 0단계에서 읽은 섹션의 질문 방식을 그대로 따라, 에이전트가 설계 파트너 역할로 두 후보의 전제를 공격하고 대안을 낸다. 원본 스킬의 실행 스크립트(`gstack-skill-start`, `gstack-paths` 등)는 쓰지 않는다.
- 예상 쟁점은 다음과 같다.
  - 생성한 예상 문제가 실제 시험 대비나 복습에 효과가 있는가
  - 하루 10문제 웹앱이 맞는 형태인가, 더 작은 형태(아티팩트, CLI)로 충분한가
  - CCA-F와 LangChain 중 어느 쪽 문제가 더 실재하는가
- 끝나는 조건은 후보 하나와 그 선택 이유가 정해지는 것이다.

### 3단계: `interview`로 수렴

- 2단계 결과를 입력으로 준다. 이미 정한 항목은 "확정"으로 명시해 같은 질문이 반복되지 않게 한다.
- 1장의 "닫아야 할 결정" 중 남은 것을 닫는다.
- 모호성 0.2 이하에서 멈춘다. Seed는 만들지 않는다. Seed는 2단계(스펙과 설계)의 일이다.

### 4단계: 문서 반영

- 결정을 기존 문서와 `requirements.md`에 반영하라고 지시할 때 `readchk`가 작동한다. 지시가 묶음이거나 범위가 모호할 때 특히 쓸모가 있다.
- `requirements.md` 초안은 내가 검토한 뒤 확정한다.

## 4. 사전 조건과 위험

| 항목 | 내용 | 대응 |
| --- | --- | --- |
| gstack 전체 설치를 하지 않은 이유 | 슬래시 커맨드 스킬 약 55개가 전역 등록되어 계획 스킬 트리거가 충돌한다. `./setup`이 실행 파일과 자체 브라우저를 빌드한다. `CLAUDE.md`에 섹션을 추가하고 훅을 등록한다. 일부 스킬만 설치하는 옵션이 README에 없다 | 저장소를 읽기만 하고 설치하지 않는다. Bun 1.4.4는 설치되어 있지만 이번에는 쓰지 않는다 |
| `/office-hours` 단독 복사 불가 | `SKILL.md`가 `~/.claude/skills/gstack/bin/`의 스크립트, 공유 `preamble.md`, `sections/*.md`에 의존한다. `gstack-paths`가 없으면 `GSTACK_STATE_ROOT` 확인 줄에서 멈춘다 | 스킬로 등록하지 않고, 섹션 문서를 방법 참고 자료로만 쓴다 |
| 방법 차용의 한계 | 원본 스킬과 동작이 다를 수 있다. gstack 고유 기능(설계 문서 목록, 학습 기록, 질문 선호 기억)은 없다 | 평가할 때 "원본 스킬이 아닌 방법 차용"임을 명시한다. 받은 커밋 해시를 기록한다 |
| 질문 중복 | `/office-hours`와 `interview` 둘 다 사용자에게 질문한다 | 3단계 입력에 확정 항목을 명시한다 |
| 산출물 중복 | `/office-hours` 방식의 설계 문서와 `requirements.md`가 겹친다 | 설계 문서는 기록으로 `dev-process/`에 두고, 요구사항은 `requirements.md` 하나로 한다 |
| 미확인 사항 | builder mode와 startup mode를 가르는 기준, `interview` 결과의 저장 위치 | 실행하며 확인해 기록한다 |

## 5. 기록과 평가

기록 위치는 `docs/dev-process/01-requirements/`이다.

| 파일 | 내용 |
| --- | --- |
| `01-aim.md` | 제안된 의도, 기대와의 차이 |
| `02-office-hours.md` | 참고한 섹션 파일과 커밋 해시, 질문과 답, 바뀐 결정 |
| `03-interview.md` | 질문과 답, 모호성 점수 변화 |
| `04-retro.md` | 도구별 평가 |

도구별 평가 기준:

- 기존 문서의 열린 질문에 없던 결정을 몇 개 새로 드러냈는가
- 다른 도구와 겹친 질문이 몇 개인가
- 기존 결정을 몇 개 바꿨는가
- 걸린 시간
- 다음 프로젝트에서도 쓸 것인가
