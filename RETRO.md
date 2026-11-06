# 프로젝트 회고

작성일: 2026-11-06
상태: 확정(2026-11-06)
성격: 개인 회고. 단계 산출물(`docs/`)이 아니며 진행 중인 단계(06 QA)의 범위와 별개다.
본 문서: [design.md](docs/02-spec-design/output/design.md) 15.0, [findings.md](docs/05-evaluation-review/output/findings.md), [evaluation.md](docs/05-evaluation-review/output/evaluation.md), [01-qa.md](docs/dev-process/06-qa/01-qa.md), [skillset-by-lifecycle.md](docs/dev-process/skillset-by-lifecycle.md), 단계 계획(`docs/dev-process/NN-<stage>-plan.md`)

## 느낀 점

### 좋았던 점

- 개발 라이프사이클에 맞는 스킬을 여러 개 써 보려고 했다. 그 과정에서 개발 절차(요구사항 → 설계 → 구현 → 실험 → 평가 → QA)를 잡을 수 있었다.
- 실제로 단계별로 나눠 수행했고, 그 방식이 좋았다.
- 단계를 진행하는 자체 스킬([.claude/skills/stage/SKILL.md](.claude/skills/stage/SKILL.md), `/stage <NN> [plan|run|doc|retro]`)을 만든 것이 잘한 결정이었다.

### 구현부터는 결과물 리뷰가 어려웠다

- 요구사항(01)과 설계(02)까지는 결과물을 꽤 꼼꼼히 리뷰했다.
- 구현(03)부터는 결과물(코드)을 꼼꼼히 리뷰하기 어려웠다.
- 그래서 만들어진 내용을 이해하려고 [docs/concepts/](docs/concepts/)에 설명 문서를 따로 정리했다(2026-11-05~11-06).

| 문서 | 내용 |
| --- | --- |
| [quize-pipeline.md](docs/concepts/quize-pipeline.md) | 문제 출제 파이프라인과 개념 지도 |
| [guardrails-and-tracing.md](docs/concepts/guardrails-and-tracing.md) | 문제 검사와 기록 |
| [langchain-usage.md](docs/concepts/langchain-usage.md) | LangChain 사용 범위와 개념 매핑 |
| [reading-traces.md](docs/concepts/reading-traces.md) | Langfuse 기록 읽는 법 |
| [question-set-flow.md](docs/concepts/question-set-flow.md) | 문제 생성에서 풀 고정, 세트 구성까지 |

### 스킬은 "썼다"기보다 "차용했다"

단계마다 대표(1순위)로 꼽은 스킬은 대부분 설치하지 않고 `SKILL.md` 절차만 읽고 따랐다. 실제로 설치해 호출한 것은 ouroboros와 paperthin이다.

| 단계 | 스킬 | 사용 방식 | 근거 |
| --- | --- | --- | --- |
| 01 요구사항 | gstack `/office-hours` | 차용. 저장소를 받아 `SKILL.md`, `sections/`를 읽고 질문 방식만 따랐다 | [01-requirements-plan.md](docs/dev-process/01-requirements-plan.md) 26, 77~79행 |
| 01 요구사항 | ouroboros `interview` | 실제 호출(MCP) | `01-requirements-plan.md` 27행 |
| 02 설계 | ouroboros `seed`, `qa` | 실제 호출(`ouroboros_generate_seed`, `ouroboros_qa`) | [02-spec-design-plan.md](docs/dev-process/02-spec-design-plan.md) 35, 101~102행 |
| 02 설계 | superpowers `brainstorming`, `writing-plans` | 쓰지 않음 | `02-spec-design-plan.md` 43행 |
| 03 구현 | superpowers(TDD, worktree, subagent) | 쓰지 않음. TDD는 `CLAUDE.md` 작업 규칙, 진행은 프로젝트 내장 stage 스킬로 대신했다 | [skillset-by-lifecycle.md](docs/dev-process/skillset-by-lifecycle.md) "이 프로젝트의 선택" |
| 04 실험 | pstack `/arena` | 차용. 설치본의 모델 설정과 교차 Judge가 Cursor 기준이라 이 환경에서 쓸 수 없었다 | `skillset-by-lifecycle.md` 단계별 추천 4행 |
| 04·05 | paperthin `mandela` | 실제 호출 | `skillset-by-lifecycle.md` "이 프로젝트의 선택" |
| 05 평가 | ouroboros `evaluate` | 실제 호출 | `skillset-by-lifecycle.md` 단계별 추천 5행 |
| 05 평가 | pstack `/interrogate` | 차용 | `skillset-by-lifecycle.md` 단계별 추천 5행 |
| 06 QA | gstack `/qa`, superpowers `verification-before-completion` | 둘 다 차용 | [06-qa-plan.md](docs/dev-process/06-qa-plan.md) 51, 57~58, 74행 |

정리:

- 실제로 쓴 것: ouroboros(`interview`, `seed`, `qa`, `evaluate`), paperthin(`mandela` 등), 프로젝트 내장 stage 스킬
- 절차만 차용한 것: gstack(`/office-hours`, `/qa`), pstack(`/arena`, `/interrogate`), superpowers 검증 스킬
- 쓰지 않은 것: superpowers 본체. 처음에는 기본 도구로 정했었다

차용한 이유는 대부분 환경 문제였다.

- gstack: 설치하면 슬래시 커맨드 약 55개가 전역 등록되어 계획 스킬끼리 트리거가 충돌한다. Windows 지원이 최소 수준이다.
- pstack: Cursor 기준이라 모델 설정과 교차 Judge를 이 환경에서 쓸 수 없다.

그래서 이 프로젝트의 실제 뼈대는 외부 스킬이 아니었다. 단계 구분(`skillset-by-lifecycle.md`), `TASKS.md`의 `확인:` 줄, stage 스킬, 단계 끝마다 한 회고가 뼈대였다.

차용의 한계는 01 계획에 이미 적었다. 원본 스킬과 동작이 다를 수 있고, 원본의 고유 기능(설계 문서 목록, 학습 기록, 질문 선호 기억)은 없다.

## Claude 평가

2026-11-06 회고 대화에서 Claude(claude-opus-5-5)가 낸 평가다.

### 진행 과정

AI가 만드는 속도가 사람이 검증하는 속도를 앞질러 간 과정이다. 일정과 산출물은 잘 마쳤지만, 시간과 사람의 주의를 쓴 곳은 위험이 있던 곳과 거꾸로였다.

| 날짜 | 커밋 | 한 일 |
| --- | --- | --- |
| 2026-11-03~11-04 | 10 | 도구 조사, 요구사항(01), 설계(02). 사람이 꼼꼼히 리뷰한 구간 |
| 2026-11-05 | 119 | 구현(03) M0~M6 전부, 실험(04)까지 하루에 끝냄 |
| 2026-11-06 | 36 | 평가(05)와 QA(06)를 병렬로. 마감이 17:00에서 13:30으로 당겨짐 |

- 구현이 예상보다 훨씬 빨랐다. M0 목표는 11-05 17:00이었는데 실제로는 09:41에 끝났다. AI 개발에서 코드 생성은 병목이 아니었다.
- 병목은 검증과 이해였다. 03부터 리뷰가 어려워져 `docs/concepts/`를 만들었다. 샌드박스 탈출, 정답 위치 쏠림, 동시성 문제는 05·06에서야 드러났다.
- 구현에서 앞선 시간이 검증으로 넘어가지 않았다. 여유는 작업 추가(T2.10, T2.11, T4.7~T4.9)와 실험(04)에 쓰였다. 마감이 당겨지자 05는 "높음만 수정"으로 줄었고 중간 심각도 10개는 기록만 남았다.
- 목표 범위는 넘겼다. 원래 목표는 5단계까지였고 6단계는 "시간이 남으면"이었다. 05와 06을 병렬로 돌려 6단계까지 했다.

### 잘한 점

- 회고가 실제로 다음 단계를 바꿨다. 03·04·05 회고의 수정안이 매번 `skillset-by-lifecycle.md`에 반영됐다. 예를 들어 "`mandela`는 모델 호출 전에 돌린다"는 04 회고에서 나왔고, 05에서 누수 3개를 미리 잡았다.
- 결정 기록 습관이 확실했다. 설계와 다르게 정한 값은 "결정" 표에 적고 승인 뒤 design.md를 고쳤다(개정 이력 15개). 확인하지 못한 것은 "미확인"으로 남겼다. 그래서 회고할 때 근거를 바로 찾을 수 있었다.
- 평가 방식에서 의미 있는 비교를 얻었다. 05에서 기준 증명(`evaluate`)은 발견 0개, 공격자 방식은 14개(높음 5개 전부)였다. 기준 통과가 결함 없음은 아니라는 것을 데이터로 보였다.

### 아쉬운 점

- 코드는 사실상 사람 리뷰 없이 지나갔다. 앱, 테스트, Judge, 평가자, 공격자가 모두 같은 모델 계열이었다([evaluation.md](docs/05-evaluation-review/output/evaluation.md) 6.1). 바깥 진실은 실제 실행, 본인 감사 20문항, 다른 계열 교차 풀이뿐이었다. `docs/concepts/`는 모델이 코드를 보고 쓴 설명이라 "무엇을 하는지"는 알려 줘도 "맞게 하는지"는 검증하지 못한다.
- 리뷰가 "빠진 것"을 잘 잡지 못했다. 정답 위치 쏠림(F-20)은 설계서에 보기 순서 규칙이 없어서 생겼고, 06 사전 QA에서야 드러났다. 샌드박스 격리도 03에서 기술 부채로 넘겼다가 05에서 `.env` 반출로 재현됐다. 01·02 리뷰는 적힌 내용을 꼼꼼히 봤지만 "있어야 할 것이 없는지"는 묻지 않았다.
- 문서에 든 비용이 컸다. design.md가 이틀 만에 15판까지 갔고, 단계마다 계획·기록·회고가 있었다. 미니 프로젝트치고 무거웠다.

### 자체 stage 스킬

근거: [.claude/skills/stage/SKILL.md](.claude/skills/stage/SKILL.md), 그 커밋 이력, `templates/retro.md`

잘된 점:

- 도구와 진행 절차를 분리했다. "이 스킬에는 도구 이름을 적지 않는다"(17행). 도구 선택은 `skillset-by-lifecycle.md`가, 진행은 스킬이 맡았다. 그래서 절차만 차용한 도구와 실제로 호출한 도구를 같은 틀에 끼울 수 있었다.
- 상태를 파일에 두어 세션이 끊겨도 이어졌다. 계획의 상태 줄, 기록 파일의 "인계" 절, `TASKS.md` 체크박스로 다음 모드를 판정한다. 대화가 끊기거나 압축돼도 `/stage NN run` 한 번으로 재개됐다.
- 멈추는 지점이 정해져 있었다. 계획 승인, 최종 문서 확정, lifecycle 수정안 승인에서 사람을 기다린다. retro가 lifecycle 문서를 직접 고치지 않고 수정안만 내게 한 규칙(142행)이 "회고가 다음 단계를 바꾼" 반복을 만들었다.
- 쓰면서 스킬 자체가 나아졌다. 2026-11-05 09:55 세션 인계·병렬 실행 규칙, 10:13 워커 커밋 해시 기록과 병합 전 기준 확인 규칙을 더했다. 후자는 격리 worktree가 기본 브랜치에서 갈라지는 문제를 겪고 나서 더했다.
- 사용자가 직접 부를 때만 동작한다(`disable-model-invocation: true`). 다른 계획 스킬과 트리거가 충돌하지 않는다.

아쉬운 점:

- 사람 리뷰 지점이 문서에만 있다. 승인을 기다리는 곳은 계획과 최종 문서뿐이다. `run`의 검증은 `확인:` 줄과 테스트이고, 둘 다 모델이 돌린다. 03부터 리뷰가 어려웠던 것은 이 구조 때문이기도 하다.
  - 개선안: `run` 단계 끝에 "위험 모듈 diff와 테스트 사례 표를 보이고 승인받기"를 둔다.
- retro 범위가 단계 하나다. 템플릿은 도구별 평가, 계획 대비, lifecycle 수정안, 다음 단계로 넘길 것뿐이다. 단계 사이의 시간 배분(구현에서 번 시간이 검증으로 넘어가지 않은 것)은 어느 단계 회고에도 잡히지 않는다. 이 문서가 그 빈칸을 채운다.
- `doc` 모드 규칙이 무겁다. 버전 규칙, 추적표, 과정 기록 분리로 정확성은 높였지만, design.md가 이틀 만에 15판이 된 문서 비용과 이어진다.
- 문구가 차용 방식과 맞지 않는다. `run` 4.2는 "스킬은 Skill 도구로 부른다"인데, 실제로는 대부분 `SKILL.md` 절차만 따랐다. "절차만 따르는 경우"를 규칙에 넣으면 실제와 맞는다.

### 다음에 해 볼 것

- 구현이 빠르다는 것이 확인되면, 그 여유를 기능 추가보다 검증과 사람 리뷰에 먼저 쓴다.
- 03부터는 코드를 다 읽지 말고 사람이 볼 표면을 좁힌다.
  - 작업마다 `확인:` 줄과 테스트 사례 표를 읽고 "이 사례가 맞나"만 판단한다.
  - 위험이 큰 모듈(채점, 검사, 샌드박스)만 diff를 직접 본다.
- 설계 리뷰에 "이 종류의 앱이면 보통 있어야 하는데 없는 것은?"을 한 번 묻는다. 사람이 해도 되고, 맥락 없는 서브에이전트에게 물어도 된다.

## 설계 개선점

| # | 개선점 | 개선 방법 | 이미 지적된 곳 | 개선 완료 여부 |
| --- | --- | --- | --- | --- |
| 1 | 정답 위치가 A에 쏠렸다. "늘 A"만 골라도 단일·코드 29문항 중 25개를 맞힌다 | 세트를 낼 때 서버가 보기 순서를 섞는다. 또는 생성할 때 정답 위치를 고르게 나눈다 | 05 [findings.md](docs/05-evaluation-review/output/findings.md) F-20, [evaluation.md](docs/05-evaluation-review/output/evaluation.md) 6.1 | 추후 개선 |
| 2 | 감사에서 떨어진 문제가 다시 고정하기 전까지 계속 출제된다 | 세트를 만드는 코드(`sets.compose`)가 `status='passed'`인 문제만 고르게 한다 | 05 findings.md 3절 "남은 한계" | 추후 개선 |
| 3 | 감사 화면이 표본 20문항의 정답을 보여 준다. 풀의 3분의 1이 정답이 보인 채 출제된다(FR-2.1과 충돌) | 감사한 문항을 출제에서 빼거나 우선순위를 낮춘다. 또는 감사 전용 풀을 따로 둔다 | 05 findings.md 4절 관찰, evaluation.md 6.1 | 추후 개선 |
| 4 | 오답 제출과 새 세트 생성이 동시에 오면 둘 다 통과한다. 그 오답은 태그를 못 단다. 같은 문제를 동시에 다시 내거나 세트를 동시에 만들면 500 오류가 난다 | 확인과 쓰기를 한 트랜잭션(`BEGIN IMMEDIATE`)으로 묶는다. 제약 위반은 409로 바꿔 돌려준다 | 05 findings.md F-9, F-10 | 추후 개선 |
| 5 | 샌드박스가 같은 프로세스 안의 방어라서 결과 줄 위조가 남아 있다 | 결과를 물려받은 파일 기술자가 아닌 별도 채널로 돌려받는다. 운영체제 수준 격리(컨테이너 등)를 쓴다 | [design.md](docs/02-spec-design/output/design.md) 8.2 "한계", 05 findings.md F-6, evaluation.md 6.1 | 추후 개선 |
| 6 | 생성 모델(Sonnet 4.6)과 Judge(Sonnet 4.5)가 같은 계열이다. 둘이 같이 틀리면 `version_conflict`(라이브러리 버전 문제)로 잘못 분류된다 | 실행 결과와 정답 키가 다를 때만 다른 계열 모델(Nova, gpt-oss)로 한 번 더 판정한다 | 05 findings.md F-13, evaluation.md 6.1 "같은 계열 검토"(위험만 기록, 방법은 미기록) | 추후 개선 |
| 7 | 문제를 보충해 다시 고정하면 풀 ID가 바뀌어 감사 20문항을 처음부터 다시 해야 한다. 이미 검토한 문항이 또 뽑히거나 새 문항이 빠질 수 있다 | 감사 결과를 문항 단위로 이어받는다. 새 표본은 검토하지 않은 문항에서 먼저 뽑는다 | 없음(이번에 새로 찾음) | 추후 개선 |
| 8 | 다시 고정하면 `baseline.json`의 `sets`에서 지난 풀이 기록이 빠져 학습 추이가 끊긴다 | 세트마다 `pool_snapshot_id`를 붙여 전부 남긴다 | 없음(이번에 새로 찾음) | 추후 개선 |
| 9 | 변형 문제는 풀 밖이라 감사를 받지 않는다. Judge만 보고 출제된다 | 변형 배치에도 작은 감사 표본을 둔다. 또는 교차 풀이를 통과해야만 낸다 | 없음. 05 수용 기준 7은 변형 데이터가 없어 면제됐다 | 추후 개선 |
| 10 | 출처 원문을 다시 받아 최신 문서와 비교하는 절차가 없다. 문서가 바뀌어도 알 수 없다 | `snapshot fetch --check`로 최신 문서와 해시를 비교한다. 바뀐 페이지를 근거로 쓰는 문제를 표시한다 | 없음(이번에 새로 찾음) | 추후 개선 |
| 11 | 새 문제가 떨어져도 화면과 지표에 신호가 없다. 앱은 예전 문제로 조용히 세트를 채운다 | API와 화면에 남은 새 문제 수를 보여 준다. 기준 아래로 내려가면 보충을 안내한다 | 06 [01-qa.md](docs/dev-process/06-qa/01-qa.md) IMP-4(기록만) | 추후 개선 |

### 우선순위

- 먼저 고칠 것: 1번. 학습 효과를 직접 깎는다.
- 풀을 보충하는 순간 드러나는 것: 2, 7, 8, 9번.
- 풀을 오래 쓸수록 커지는 것: 6, 10번.
