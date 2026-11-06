# 06 QA 단계 실행 계획

상태: 승인 (2026-11-06). 결정 1은 추천안, 결정 2는 "화면 버그 다 수정", 결정 3은 "설치 없이 최대한 절차 따르기"
작성일: 2026-11-06
수정: 2026-11-06 11:27. 사용자 지시로 병렬 진행한다. 화면 수정(Q-1 화면 쪽, Q-2, "세트 N를" 조사, `**` 굵게, IMP-1·IMP-2 말풍선)은 워커 W1(격리 worktree, 기준 `b34d5d2`)이 1단계와 동시에 한다. gstack 순서(발견 목록을 먼저 보고한 뒤 수정)와 다르다. W1 병합은 브라우저 시험과 기준 건강 점수 측정이 끝난 뒤에 한다(Vite가 화면을 다시 불러오기 때문). 3장 "병렬 실행" 표는 이 줄로 바꾼다: 1단계 코디네이터(브라우저 시험, TC-11), 2단계 W1(`web/src/`). TC-11은 이 지시를 받기 전(11:22~11:24)에 API로 이미 돌렸다. 11:07에 8001 서버가 같은 `scratch.db`에 세트를 만들어 시험이 섞였다. 그래서 11:10부터 전용 DB `data/experiments/qa06.db`(`qa-base.db` 사본)로 8002를 다시 띄웠다
수정: 2026-11-06 11:00. run 0단계에서 8001, 5174에 10:42에 띄워진 서버가 이미 있었다(같은 scratch 풀). 멈추는 명령이 권한 분류기에 막혀 그대로 두고, 이 단계 서버를 API 8002, 웹 5175(`web/node_modules/.scratch/vite.qa06.config.mjs`)로 따로 띄웠다. 서버 로그는 `data/experiments/qa-logs/`(git 제외)에 남긴다
수정: 2026-11-06 11:00. 사용자 결정을 반영했다. (결정 2) 화면 코드(`web/`)에서 고칠 수 있는 버그는 심각도와 관계없이 모두 고친다. 1단계에서 새로 찾은 것도 포함한다. 서버·채점·데이터를 바꿔야 하는 버그(F-10 서버 쪽 500, F-20 정답 쏠림)는 기록만 한다. 12:50 시간 제한은 둔다. (결정 3) gstack `qa/` 디렉토리의 나머지 절차 파일(`sections/exploratory.md`, `sections/qa-patterns.md`, `sections/scope.md`, `sections/browser-verify.md`, `references/issue-taxonomy.md`, `templates/qa-report-template.md`)을 2026-11-06에 읽고 2장 "gstack 절차 적용표"에 반영했다. 건강 점수 기준표를 읽었으므로 건강 점수를 쓴다
대상: [input/pre-qa-findings.md](../06-qa/input/pre-qa-findings.md) 1개. 05 확정 문서 [evaluation.md](../05-evaluation-review/output/evaluation.md) 1.1과 근거 자료 [findings.md](../05-evaluation-review/output/findings.md)
근거: [skillset-by-lifecycle.md](skillset-by-lifecycle.md)의 "6. QA" 행. gstack README와 `qa/SKILL.md`, superpowers `skills/verification-before-completion/SKILL.md`를 2026-11-06에 다시 읽었다.

## 쉬운 설명

이 절은 계획 전체를 쉬운 말로 줄인 것이다. 자세한 값은 1장부터 있다.

### 이 단계에서 하는 일

05는 "약속대로 되는가"를 증거로 확인했다. 06은 실제 브라우저에서 사용자처럼 앱을 눌러 보고, 화면에서 나는 버그를 찾아 고친다. 크게 셋을 한다.

1. **시나리오 실행**: 요구사항에서 뽑은 테스트 케이스 17개(세트 시작, 형식 4개 풀이, 오답 태그, 복습, 새 문제 소진, 감사 화면, 모바일 폭 등)를 브라우저에서 하나씩 돌린다. 사전 QA가 아직 보지 않은 곳도 여기에 넣었다.
2. **버그 고치기**: 결정 2에서 정한 범위만 고친다. 고치기 전에 실패하는 테스트를 먼저 쓴다.
3. **다시 확인**: 고친 버그를 처음 재현한 방법 그대로 다시 돌려 막혔는지 본다. 전체 테스트도 다시 돌린다.

### 어떤 DB를 쓰나

| 용도 | DB | 이유 |
| --- | --- | --- |
| 화면 시나리오, 버그 재현, 수정 확인 | `data/experiments/scratch.db`(53문항, 풀이 기록 0) | 화면 버그는 문제 내용과 관계없이 같은 코드로 돈다 |
| 평가 대상 풀의 문제 내용 확인(정답 쏠림 등) | `data/quiz.db`를 읽기 전용(`mode=ro`)으로 조회 | 05에서 평가받고 커밋한 제출본이다. 풀이 기록이 쌓이면 제출본이 바뀐다 |

`scratch.db`는 시나리오를 돌리면 풀이 기록이 쌓인다. 깨끗한 상태가 필요한 시나리오 전에는 처음 사본에서 다시 복사한다.

### 이미 알려진 버그 3개

사전 QA(계획 전 한 번 훑어본 것)에서 찾았다. 둘은 05에도 같은 내용이 있어 05 ID로 추적한다(05 판정 6.2 조건).

| 사전 QA | 내용 | 05 ID | 05 심각도 |
| --- | --- | --- | --- |
| Q-1 | "새 세트 시작"을 빠르게 두 번 누르면 500 오류가 나거나 세트가 두 개 생긴다 | F-10 | 중간, 기록만 |
| Q-2 | 화면이 지난 세트에 묶이면 빠져나갈 버튼이 없다 | 없음(새 발견) | - |
| Q-3 | 정답이 거의 늘 A다 | F-20 | 중간, 기록만 |

## 1. 목표

- **입력**: [pre-qa-findings.md](../06-qa/input/pre-qa-findings.md), [evaluation.md](../05-evaluation-review/output/evaluation.md) 6.2 판정 조건, [findings.md](../05-evaluation-review/output/findings.md) F-1~F-20, [requirements.md](../01-requirements/output/requirements.md) FR-1~FR-9
- **산출물**: `docs/06-qa/output/test-cases.md`(TC 목록, 절차, 결과, 증거), `docs/06-qa/output/defects.md`(DEF 목록, 재현, 상태, 수정 커밋)
- **최종 문서**: `docs/06-qa/output/qa-report.md`. 테스트 완료 보고서(`.claude/skills/stage/templates/output-types.md`의 06 행). `doc` 모드에서 쓴다.
- **부산물**: 도구별 사용 기록과 평가. `docs/dev-process/06-qa/`에 둔다.
- **닫아야 할 결정**:
  1. **DB**: 위 "어떤 DB를 쓰나" 표대로 한다. 평가 대상 60문항으로 화면까지 볼 필요가 생기면 `data/quiz.db`를 `data/experiments/qa-prod.db`로 복사해 쓴다. 추천: 표대로. 지금 시나리오 중에는 60문항 화면이 필요한 것이 없다.
  2. **수정 범위**(닫음, 2026-11-06 11:00): 화면 코드(`web/`)에서 고칠 수 있는 버그는 심각도와 관계없이 모두 고친다. 지금 알려진 것은 Q-1의 화면 쪽(두 번째 클릭 막기)과 Q-2(`set_closed`에서 빠져나가기)다. 1단계에서 새로 찾은 화면 버그도 고친다. 높음은 위치와 관계없이 고친다. 서버·채점·데이터를 바꿔야 하는 중간 이하 버그(F-10 서버 쪽 500, Q-3/F-20 정답 쏠림)는 기록만 한다. 12:50까지 못 끝낸 수정은 "보류"로 기록한다.
  3. **도구 설치**(닫음, 2026-11-06 11:00): gstack과 superpowers는 설치하지 않는다. gstack `qa/` 절차 파일을 모두 읽고 설치 없이 할 수 있는 단계는 모두 따른다(2장 "gstack 절차 적용표"). 설치본 도구(마감 가드, 증거 기록기, `$B`/Aside 브라우저)는 Orca 내장 브라우저와 손 기록으로 대신한다. superpowers 검증 스킬도 절차만 따른다.

## 2. 도구별 역할

| 도구 | 역할 | 입력 | 출력 | 이 환경 상태 |
| --- | --- | --- | --- | --- |
| gstack `/qa`(절차만) | 기준 탐색 → 발견 목록 → 버그마다 재현, 회귀 테스트 먼저, 최소 수정, 재확인, 버그마다 커밋 | TC 목록, 실행 중인 앱(`http://localhost:5174`) | TC 결과, DEF 목록, 수정 커밋 | 미설치(2026-11-06 확인. `~/.claude/plugins/installed_plugins.json`, `~/.claude/skills`에 없음) |
| superpowers 검증 스킬(`verification-before-completion`, 절차만) | "고쳤다", "통과한다"를 말하기 전에 그 주장을 증명하는 명령을 새로 돌리고 출력을 읽는다. 회귀 테스트는 수정을 되돌려 실패를 보고 다시 넣어 통과를 본다 | 수정 커밋, 처음 재현 절차 | 기록 파일의 확인 줄 | 미설치(2026-11-06 확인) |
| Orca 내장 브라우저(실행 환경) | 화면 조작, 스냅샷, 콘솔 실행 | TC 절차 | 화면 상태, 콘솔 출력 | 사용 가능. `orca --version` 1.4.247, `orca tab list` 응답(2026-11-06 10:50 확인) |

실행 환경 값:

| 항목 | 값 |
| --- | --- |
| API | `app/`에서 `QUIZ_DB=../data/experiments/scratch.db uv run uvicorn quiz.server:app --port 8001`. `AWS_*`, `LANGFUSE_*`가 없는 셸에서 띄운다 |
| 웹 | `web/`에서 `npx vite --config node_modules/.scratch/vite.config.mjs`(5174, `/api`를 8001로 넘김). git 제외 위치의 임시 설정이다. 내용은 기록 파일에 옮겨 둔다 |
| 화면 테스트 | 화면 컴포넌트 테스트 도구는 없다. 순수 함수만 `node --test`로 돈다(`web/src/*.test.ts`). 화면 수정은 판단 로직을 순수 함수로 빼서 그 함수에 테스트를 먼저 쓴다 |

고르지 않은 도구:

- gstack 설치: "이 프로젝트의 선택" 절이 Windows 마찰로 gstack을 쓰지 않는다고 했다. README는 Windows를 "최소 지원"이라 하고, 설치가 `~/.claude/skills/gstack` 등록, `CLAUDE.md`에 gstack 절 추가, Bun 빌드와 자체 Chromium을 요구한다. 마감(13:30)까지 남은 시간이 약 2시간 40분이라 설치 문제를 풀 여유가 없다.
- gstack 보고서 위치 `.gstack/qa-reports/`, 텔레메트리, 학습 기록(`eureka.jsonl`), `TODOS.md` 갱신: 쓰지 않는다. 산출물은 `docs/06-qa/output/`에 둔다.

gstack 절차 적용표(2026-11-06 읽은 `qa/` 파일 기준):

| gstack 절차 | 출처 | 이 단계에서 하는 방법 |
| --- | --- | --- |
| 모드 Full(URL 있음, 도달 가능한 화면 전부), 수정 등급 Standard | `SKILL.md`, `qa-patterns.md` "Modes" | 화면은 풀이 화면, 결과·태그, 세트 끝, 감사 화면(`#audit`), API 문서(`/docs`)다. 수정 범위는 결정 2가 등급보다 우선한다 |
| 깨끗한 작업 트리에서 시작 | `SKILL.md` Setup | 0단계 1번 |
| 행동마다 charter(계약, 위험, 진입점, 격리, 끝 조건, 출처, 입력) | `exploratory.md` 1 | TC마다 charter 한 줄을 `01-qa.md`에 쓴다 |
| 탐색은 블랙박스. 탐색 중 소스를 읽지 않는다 | `qa-patterns.md` "Important Rules" | 1단계에서 `web/src`, `app/quiz`를 읽지 않는다. 원인 분석은 2단계에서 한다 |
| 기준 먼저: 도전 전에 정상 결과와 상태를 본다 | `qa-patterns.md` Phase 3, `exploratory.md` 2-1 | TC-1~TC-3을 먼저 돌린다 |
| probe 하나씩, 다음 probe 전에 체크포인트(`observationCommand`, `observed`, `hypothesis`, `nextCommand`) 작성. 묶어 돌리지 않는다 | `exploratory.md` 2-2 | 체크포인트를 `docs/dev-process/06-qa/probes/exploration-NNN.json`에 Write로 쓴다. 덮어쓰지 않는다 |
| 상호작용마다 콘솔 오류 확인 | `qa-patterns.md` Phase 3 | 화면을 열 때 오류 수집 훅을 넣고 probe마다 `orca eval`로 읽는다 |
| 링크 확인(같은 출처 HEAD) | `qa-patterns.md` Phase 3 "Links" | `orca eval`로 링크 목록을 뽑아 `curl -I`로 본다 |
| 모바일 375×812 | `qa-patterns.md` Phase 4 | TC-13. 뷰포트 설정이 안 되면 "차단"으로 적는다 |
| 문제는 같은 초기 상태에서 같은 명령으로 한 번 더 재현해 확정하고 최소화한다 | `exploratory.md` 2-4, `qa-patterns.md` Phase 5 | `qa-base.db`에서 복사한 상태로 다시 돌린다. 다른 입력이나 회귀 테스트는 재현으로 치지 않는다 |
| 스크린샷 증거(전·후) | `qa-patterns.md` Phase 5, 보고서 템플릿 | `orca screenshot`으로 `docs/06-qa/output/screenshots/issue-NNN-*.jpg`에 둔다 |
| 수정 전에 기준 발견을 보고 | `SKILL.md` | 1단계 끝에 DEF 목록과 기준 건강 점수를 사용자에게 보인다 |
| 심각도·범주 분류 | `issue-taxonomy.md` | DEF마다 gstack 심각도(critical, high, medium, low)와 범주를 붙인다. 05 심각도(높음, 중간, 낮음)도 함께 적는다. 수정 범위와 05 추적은 05 심각도로 한다 |
| 건강 점수(범주 8개 가중 평균, 시험 안 한 범주 제외) | `qa-patterns.md` "Health Score Rubric" | 1단계 끝(전)과 3단계 끝(후)에 계산한다. `baseline.json`(`date`, `url`, `healthScore`, `issues`, `categoryScores`)을 `docs/06-qa/output/`에 둔다 |
| 버그마다 재현 → 회귀 테스트 먼저 → 최소 수정 → 재확인 → 커밋 `fix(qa): ISSUE-NNN — 설명` | `SKILL.md` Fixing | ISSUE 번호는 DEF 번호와 같게 쓴다(DEF-1 = ISSUE-001) |
| 회귀 테스트 이름 `{name}.regression-N.test.{ext}`, 머리에 출처 주석(이슈, 날짜, 보고서) | `SKILL.md` Regression tests | 예: `web/src/startGuard.regression-1.test.ts`. 가장 작은 테스트(로직은 단위 테스트)를 고른다 |
| 수정 판정 verified, best-effort, reverted. 확인 안 된 수정은 커밋하지 않는다 | `SKILL.md` | `02-fix.md`에 판정을 적는다 |
| 수정 5개마다, 되돌림 뒤 진행 점검. 되돌림 2번이거나 관련 없는 파일을 고치면 멈춤 | `SKILL.md` Self-regulation | 그대로 따른다 |
| 기존 테스트를 약하게 하지 않음. CI 설정을 바꾸지 않음 | `SKILL.md` | 그대로 따른다 |
| 보고서 템플릿(건강 점수, 고칠 것 3개, 콘솔 상태, 심각도 수, 수정 표, 전·후 증거, 회귀 테스트 표, 출시 준비) | `templates/qa-report-template.md` | `qa-report.md`의 06 행 장에 이 항목을 나눠 넣는다 |

설치 없이 못 하는 것:

| gstack 절차 | 이유 | 대신 하는 것 |
| --- | --- | --- |
| 마감 가드(`gstack-qa-deadline`) | 설치본 도구 | 3장 시간표를 probe마다 시계로 확인한다 |
| 증거 기록기(`gstack-qa-evidence`)와 `annotations.json` 생성 | 설치본 도구 | API·DB probe는 명령과 출력을 기록 파일에 그대로 붙인다 |
| `$B`/Aside 브라우저, `annotatedScreenshot` | 설치본 도구 | Orca 내장 브라우저 `snapshot`, `screenshot`, `eval`, `click` |
| 회귀 모드(`--regression`) 비교 | 이전 gstack 기준선이 없다 | 사전 QA 결과와 비교만 한다 |

도구 설명 요약:

- gstack `/qa`: 대상은 브라우저 URL 또는 API·CLI다. 모드는 diff 기준, 전체, 빠른(`--quick`), 회귀(`--regression`)다. 수정 등급은 Quick(치명·높음), Standard(중간까지, 기본), Exhaustive(낮음까지)다. 깨끗한 작업 트리에서 시작한다. 수정 전에 기준 발견을 먼저 보고한다. 버그마다 재현 → 회귀 테스트 먼저 → 최소 수정 → 재확인 → `fix(qa): ISSUE-NNN — 설명` 커밋 하나다. 확인 안 된 수정은 커밋하지 않는다. 되돌린 수정이 2번이거나 관련 없는 파일을 고치면 멈춘다. 기존 테스트를 약하게 만들지 않는다.
- superpowers 검증 스킬: 성공을 말하기 전에 증명 명령을 정하고, 새로 끝까지 돌리고, 출력과 종료 코드를 읽고, 출력이 주장을 뒷받침할 때만 말한다. "버그 고침"의 증거는 원래 증상을 다시 해 본 결과다. 회귀 테스트의 증거는 빨강-초록 순환이다. 에이전트의 "성공" 보고는 증거가 아니다.

## 3. 진행 순서

시간표(마감 13:30):

| 단계 | 목표 시각 |
| --- | --- |
| 0 사전 준비 | 11:15 |
| 1 시나리오 실행 | 12:15 |
| 2 수정 | 12:50 |
| 3 재확인 | 13:05 |
| `doc` | 13:25 |

### 0단계: 사전 준비

1. 작업 트리가 깨끗한지 본다(gstack 절차).
2. `data/quiz.db`의 sha256과 행 수를 적는다. 끝에 다시 재서 같은지 본다.
3. `data/experiments/scratch.db`를 `data/experiments/qa-base.db`로 복사한다. 깨끗한 상태가 필요한 TC 전에 이 사본을 `scratch.db`로 다시 복사한다.
4. API(8001)와 웹(5174)을 띄우고 Orca 탭을 연다. `/api/health` 응답을 본다.
5. 대상 커밋 해시를 적는다.

### 1단계: gstack `/qa` 절차로 시나리오 실행

- 입력: 아래 TC 목록. 결과는 사전 QA와 별개로 이 세션에서 다시 돌린 것만 센다.
- 하는 일: TC를 순서대로 돌린다. TC마다 결과(통과, 실패, 차단)와 증거(스냅샷 요약, 콘솔 출력, API 응답, DB 조회)를 남긴다. 실패는 DEF로 올리고 05 심각도 기준(높음, 중간, 낮음)을 붙인다. 05 발견과 같으면 05 ID를 함께 적는다. 수정 전에 DEF 목록을 사용자에게 보인다.
- 끝나는 조건: TC 17개 모두 결과가 있고, 기준 건강 점수와 `baseline.json`이 있고, DEF 목록을 사용자에게 보였다.
- 기록 파일: `01-qa.md`

| TC | 시나리오 | 관련 요구 ID | 출처 |
| --- | --- | --- | --- |
| TC-1 | 새 세트 시작: 10문제, 1번만 열림 | FR-1.1, FR-1.4 | 사전 QA |
| TC-2 | 풀이 전 화면과 네트워크 응답에 정답 키·해설·주제가 없다 | FR-2.1 | 05 기준 |
| TC-3 | 단일 선택 정답: 정답 여부, 한국어 해설, 구절 매핑 표, 근거 링크·인용 | FR-2.2, FR-2.3 | 사전 QA |
| TC-4 | 복수 선택: 고를 개수 안내, 일부만 맞으면 오답 | FR-3.1 | 사전 QA 미확인 |
| TC-5 | 단답: 대소문자·공백·백틱·끝 `()` 정규화 | FR-3.2 | 사전 QA |
| TC-6 | 코드 선택: 코드 블록 표시, "코드 보기"가 공식 문서를 연다 | FR-2.4 | 사전 QA 미확인 |
| TC-7 | 오답 → 독해 실수 → 구절 선택 → 저장. 태그 전 "다음 문제" 잠김 | FR-4.1, FR-4.2 | 사전 QA |
| TC-8 | 오답 → 개념 실수 → 저장. 변형 문제 없음(면제)이면 원래 문제가 복습으로 나온다 | FR-4.1, FR-5.6 | 사전 QA 미확인 |
| TC-9 | 태그 전 새로고침 → 같은 문제 태그 입력으로 복원 | FR-8.1 | 사전 QA |
| TC-10 | 세트 끝 → 새 세트. 2세트 뒤 오답이 "복습"으로 최대 3개 | FR-5.1, FR-5.4 | 사전 QA |
| TC-11 | 새 문제 소진 뒤(53문항 풀) 세트가 복습·맞힌 문제로 채워진다 | FR-1.5 | 사전 QA 미확인 |
| TC-12 | 감사 화면(`#audit`): 목록 20문항, 결과 저장 | FR-9.1, FR-9.2 | 사전 QA 미확인 |
| TC-13 | 모바일 폭(390px)에서 문제, 보기, 결과, 태그가 가로 스크롤 없이 보인다 | FR-2.2 | 사전 QA 미확인 |
| TC-14 | "새 세트 시작" 같은 틱 두 번 클릭 | - | Q-1, F-10 |
| TC-15 | 지난 세트를 연 화면에서 답 제출, 탭 두 개에서 각각 세트 시작 | - | Q-2 |
| TC-16 | 평가 대상 풀 정답 위치 분포(`data/quiz.db` 읽기 전용) | FR-3.1 | Q-3, F-20 |
| TC-17 | API 문서 화면(`/docs`)이 프록시로 열린다 | - | CLAUDE.md 명령 표 |

TC-11은 세트 6개 이상을 풀어야 한다. 화면으로는 세트 1~2만 풀고 나머지는 같은 서버에 API로 답한다. 결과에 어느 부분이 화면 조작이었는지 적는다.

### 2단계: gstack `/qa` 절차로 수정

- 입력: 1단계 DEF 목록과 결정 2의 수정 범위
- 하는 일: DEF마다 재현 → 테스트 먼저(순수 함수 `node --test` 또는 `uv run pytest`) → 실패 확인 → 최소 수정 → 테스트 통과 → DEF 하나당 커밋 하나. 범위 밖 DEF는 "기록만"으로 둔다. 되돌림이 2번이면 멈추고 묻는다.
- 끝나는 조건: 범위 안 DEF가 모두 수정 커밋을 가지거나, 12:50에 "기록만"으로 돌렸다.
- 기록 파일: `02-fix.md`

### 3단계: superpowers 검증 절차로 재확인

- 입력: 2단계 수정 커밋, 1단계 재현 절차
- 하는 일: 고친 DEF마다 처음 재현 절차를 브라우저에서 다시 돌린다. 회귀 테스트는 수정을 되돌려 실패, 다시 넣어 통과를 본다. `app/`에서 `uv run pytest`, `web/`에서 `npm run build`와 `node --test src/*.test.ts`를 새로 돌린다. `data/quiz.db` sha256이 0단계 값과 같은지 본다. 고친 화면의 후 스크린샷을 찍고 건강 점수를 다시 계산한다(같은 범위로만 비교).
- 끝나는 조건: 확인 명령 출력과 전·후 건강 점수가 기록 파일에 있고, 사용자가 결과를 확인했다.
- 기록 파일: `03-verify.md`

### 병렬 실행

결정 2가 (나)일 때 두 수정은 같은 파일(`web/src/App.tsx`)을 바꾼다. 그래서 워커로 나누지 않고 코디네이터가 순서대로 한다. 브라우저 확인과 Orca 탭도 코디네이터 worktree에 묶여 있다.

| 단계 | 줄 | 작업 | 소유 파일 | 선행 | 실행 위치 |
| --- | --- | --- | --- | --- | --- |
| 1~3 | 코디네이터 | TC-1~TC-17, DEF 수정, 재확인 | `web/src/`, `app/quiz/`(범위 안 DEF만), `docs/` | - | 이 worktree |

## 4. 사전 조건과 위험

| 항목 | 내용 | 대응 |
| --- | --- | --- |
| 마감 | 2026-11-06 13:30. 계획 작성 시각 10:50 | 시간표를 넘기면 남은 TC를 "차단(시간)"으로 적고 수정 범위를 (가)로 줄인다 |
| 제출 DB 보호 | `data/quiz.db`는 05에서 평가받고 커밋한 제출본이다 | 서버는 항상 `QUIZ_DB`를 준다. 0단계와 3단계에 sha256을 비교한다. 다르면 `git checkout data/quiz.db`로 되돌리고 기록한다 |
| 서버 환경 변수 | 서버는 자기 환경을 지우지 않는다(05 관찰) | `AWS_*`, `LANGFUSE_*`가 없는 셸에서 띄운다. `.env`를 읽지 않는다. 이 단계는 Bedrock을 부르지 않는다 |
| 화면 테스트 도구 없음 | 컴포넌트 테스트를 먼저 쓸 수 없다 | 판단 로직을 순수 함수로 빼서 `node --test`로 테스트한다. 렌더링 확인은 브라우저 재확인으로 한다 |
| gstack 미설치 | 절차만 따른다(결정 3) | 설치본 도구가 맡던 일은 2장 "설치 없이 못 하는 것" 표대로 대신한다 |
| 임시 웹 설정 | `web/node_modules/.scratch/vite.config.mjs`는 git 밖이다. `npm ci`나 새 worktree에서 사라진다 | 내용을 기록 파일에 옮겨 둔다. 사라지면 같은 내용으로 다시 만든다 |
| `scratch.db` 상태 | 시나리오를 돌리면 풀이 기록이 쌓인다 | `qa-base.db` 사본에서 다시 복사한다. 사전 QA 상태는 `scratch-preqa.db`에 따로 있다 |
| Orca 브라우저 같은 틱 클릭 | 콘솔에서 `click()` 두 번으로 재현한다. 사람 손 더블클릭과 같은지는 미확인 | 재현 방법을 그대로 적는다 |
| 05와 같은 버그 | 05 판정 6.2 조건 | 05 ID로 추적한다. DEF에는 05 ID를 같이 적는다 |

## 5. 기록과 평가

기록 위치는 `docs/dev-process/06-qa/`이다.

| 파일 | 내용 |
| --- | --- |
| `01-qa.md` | 실행 환경 값, `data/quiz.db` 해시, TC별 charter·결과·증거, DEF 목록, 기준 건강 점수 |
| `probes/exploration-NNN.json` | probe 체크포인트(gstack `exploratory.md` 2-2) |
| `02-fix.md` | DEF별 테스트, 실패 출력, 수정 커밋 |
| `03-verify.md` | 재확인 명령과 출력, 빨강-초록 확인 |
| `04-output.md` | `doc` 모드 기록 |
| `05-retro.md` | 도구별 평가 |

평가 기준은 `.claude/skills/stage/templates/retro.md`를 따른다. 이 단계에서 추가하는 기준:

- 사전 QA가 찾은 것과 이 단계에서 새로 찾은 DEF 수
- 절차만 따른 gstack `/qa`가 설치 없이 무엇을 못 했는가(건강 점수, 스크린샷, 회귀 모드)
