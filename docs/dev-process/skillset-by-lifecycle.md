# LLM 앱 개발 라이프사이클별 스킬셋 추천

작성일: 2026-11-03
수정: 2026-11-04, 단계별 추천 표에 `디렉토리` 열 추가
수정: 2026-11-05, 03 구현 회고([10-retro.md](03-implementation/10-retro.md)) 수정안 5개 반영. 3단계 실제 진행 방식, UI 테스트 도구, Bedrock 일일 토큰 한도, 공식 문서 MCP, 보조 스킬 기록
수정: 2026-11-05, 과제 범위를 적었다. 5단계까지 하고, 6단계는 시간이 남으면 한다
수정: 2026-11-05, 04 실험 회고([07-retro.md](04-prompt-model-experiments/07-retro.md)) 수정안 4개 반영. 4행 `/arena` 사용 방식, 4행 보조를 `mandela`로 교체, 실험 전 `mandela` 점검, 실험 배치 ID와 비용 재추정
수정: 2026-11-06, 05 평가 회고([07-retro.md](05-evaluation-review/07-retro.md)) 수정안 5개 반영. 5행 1순위에 `/interrogate` 추가와 역할 구분, `evaluate` 격리 사본 주의, 평가 전 `mandela` 점검, 샌드박스 탈출 확인, 마감 13:30과 6단계 병렬 진행
수정: 2026-11-06, 06 QA 회고([05-retro.md](06-qa/05-retro.md)) 수정안 5개 반영. 6행 gstack `/qa` 절차만 따르기와 Orca 브라우저, superpowers 검증 절차, QA 전용 DB·포트, 화면 수정 병렬과 병합 시점. 범위 줄의 6단계 수행
전제: LangChain / LangGraph / DeepAgents + Langfuse, 로컬 미니 프로젝트.
근거: 각 저장소 README를 읽고 정리한 내용이며, 실제 조합을 돌려 검증하지는 않았다.
paperthin(2026-11-04 추가)은 README 요약을 바탕으로 했다. 단계 매핑은 스킬 이름과 설명에서 추론한 것이고, README에 명시된 분류가 아니다. Windows 지원 여부도 확인하지 못했다.

## 도구 요약

| 도구 | 정체 | 핵심 축 |
|---|---|---|
| gstack | Claude Code용 슬래시 커맨드 모음 (역할 분담) | CEO, 엔지니어링 매니저, QA 등 역할 |
| superpowers | 자동 발동되는 스킬 기반 개발 방법론 | 브레인스토밍, 계획, TDD, 리뷰 규율 |
| ouroboros | 스펙 우선 Agent OS (MCP 서버) | 모호성 점수, 불변 Seed, 평가와 진화 루프 |
| gajae-code (`gjc`) | 독립 실행형 코딩 에이전트 하네스 | 구독 재활용, 계획 승인 게이트, 원격 승인 |
| pstack (cursor/plugins) | 스킬, 플레이북, 서브에이전트 모음 | 검증 중심, 병렬 시도(`/arena`, `/swarm`) |
| paperthin | 에이전트 스킬 모음 (MIT, `npx skills` 설치) | 산출물 재작성과 정리, 요청 이해 검증, 사실 검증, 사이클 회고. 폴더 구조: depth(단일 산출물), breadth(여러 산출물 일관성), coil(반복 사이클), mesh(다중 관점) |

## 단계별 추천

`디렉토리` 열은 `docs/` 아래 단계 폴더 이름이다. 실행 계획은 `docs/dev-process/<디렉토리>-plan.md`, 수행 기록은 `docs/dev-process/<디렉토리>/`에 둔다. 디렉토리가 `-`인 행은 단계가 아니라 여러 단계에서 함께 쓰는 도구다.

| 단계 | 디렉토리 | 1순위 | 보조 | 이유 |
|---|---|---|---|---|
| 1. 아이디어와 요구사항 | `01-requirements` | gstack `/office-hours` | ouroboros `interview`, paperthin `aim`, `readchk` | gstack은 프레이밍을 도전하고, ouroboros는 모호성을 점수로 막는다. paperthin은 데이터나 지시를 받았을 때 의도를 제안하고 이해를 검증한다. |
| 2. 스펙과 설계 | `02-spec-design` | ouroboros `seed` | superpowers `brainstorming`, `writing-plans`, paperthin `re0-plan`, `modelchk` | 수용 기준을 Seed로 고정한다. 가볍게 가려면 superpowers만 쓴다. `modelchk`는 작업에 맞는 모델 등급과 추론 강도를 정한다. |
| 3. 구현 | `03-implementation` | superpowers (TDD, worktree, subagent) | pstack `/tdd`, `/blast-radius` | 규율은 superpowers가 자동으로 강제하고, 영향 범위 분석은 pstack이 낫다. 이 프로젝트는 superpowers를 쓰지 않았다("이 프로젝트의 선택" 참고). UI 컴포넌트 테스트 도구는 0단계에서 정한다. 없으면 UI 작업은 테스트를 먼저 쓸 수 없다. |
| 4. 프롬프트와 모델 실험 | `04-prompt-model-experiments` | pstack `/arena` | paperthin `mandela` | 변형 N개를 시도해 최선을 합친다. 이 프로젝트는 `/arena`를 설치하지 않고 SKILL.md 절차만 따른다. 설치본의 모델 설정과 교차 Judge는 Cursor 기준이라 이 환경에서 쓸 수 없다. 서브에이전트가 한 모델 계열뿐이면 교차 Judge를 건너뛴다. 변형의 판정은 앱에서 A/B로 잰다. 실패 원인이 확인된 과제에서 쓴다. ouroboros `evolve`는 명세를 진화시키는 도구이고 프롬프트 A/B를 재지 않아 보조에서 뺐다. |
| 5. 평가와 리뷰 | `05-evaluation-review` | ouroboros `evaluate`(기준 증명), pstack `/interrogate`(결함 탐지) | gstack `/review`, paperthin `mandela`, `factchk`, `shower`, `sip` | 기준 충족 증명, 다중 모델 적대적 리뷰, 프로덕션 버그 탐지. paperthin은 평가 누수 점검(`mandela`), 사실 검증(`factchk`), 무맥락 재독(`shower`), 작성 직후 자가 점검(`sip`)을 더한다. `evaluate`는 기계 검사와 기준별 판정으로 충족을 증명한다. 결함은 찾지 못할 수 있다. 결함 탐지는 `/interrogate` 절차가 맡는다. 이 프로젝트는 `/interrogate`를 설치하지 않고 SKILL.md 절차만 따른다. 공격자마다 중심 영역을 나누고 예시를 주지 않는다. 05에서 발견 20개 중 `evaluate`는 0개, 공격자는 14개(높음 5개 모두)를 냈다. `evaluate`의 `working_dir`를 판정 문서를 뺀 사본으로 줘도 평가자가 원래 저장소를 읽을 수 있다. 격리가 필요하면 사본의 `CLAUDE.md`에서 문서 경로를 지우고, 근거에 사본 밖 경로가 있는지 확인한다. |
| 6. QA | `06-qa` | gstack `/qa` | superpowers 검증 스킬 | 실제 브라우저에서 버그를 재현하고 고친다. UI가 있는 앱에 유용하다. 이 프로젝트는 gstack을 설치하지 않고 `qa/` 절차 파일(`SKILL.md`, `sections/exploratory.md`, `sections/qa-patterns.md`, `references/issue-taxonomy.md`, `templates/qa-report-template.md`)만 따른다. 건강 점수 기준표는 `qa-patterns.md`에 있다. 브라우저는 Orca 내장 브라우저로 대신한다. 06에서 결함 7개 중 4개는 사전 점검이 못 찾은 것이다. superpowers도 설치하지 않고 `verification-before-completion` 절차만 따른다. 회귀 테스트는 수정을 되돌리거나 핵심 줄을 바꿔 실패를 본다. 브라우저 시험은 세션마다 전용 DB 사본과 전용 포트를 쓴다. 시작 전에 포트 주인을 확인한다. 같은 DB를 여는 서버가 둘이면 시험이 섞인다. 화면 수정은 격리 워커가 시험과 동시에 하고, 병합은 시험과 기준 점수 뒤에 한다. 개발 서버가 화면을 다시 불러오기 때문이다. |
| 7. 배포 | `07-deploy` | gstack `/ship`, `/canary` | pstack ship 플레이북, paperthin `re0-merge`, `re0-release` | PR 생성과 배포 후 모니터링. |
| 8. 운영과 회고 | `08-operations-retro` | gstack `/retro`, `/cso` | pstack `/reflect`, `/correct`, paperthin `re0-memo`, `ssotize`, `catchup` | 회고와 보안 감사. paperthin은 교훈 정리, 문서 중복 통합, 공백 후 맥락 복구를 맡는다. |
| 문서와 산출물 정리 (전 단계 공통) | - | paperthin `re0`, `debloat`, `ssotize` | paperthin `detool`, `dedash`, `reorder` | 반복 작업 후 산출물을 최신 v0로 정리하고, 흩어진 사실을 한 곳으로 모은다. |
| 장시간 무인 작업 | - | gajae-code | ouroboros `ralph`, pstack 야간 실행 플레이북, paperthin `re0-loop`, `nba` | 원격 승인과 구독 재활용이 필요할 때. `re0-loop`는 build, QA, 회고를 반복하고 `nba`는 다음 행동 하나를 고른다. |

## 이 프로젝트(로컬 미니 프로젝트)의 선택

- 범위: 과제 목표는 5단계(평가와 리뷰)까지다. 6단계(QA)는 2026-11-06에 했다(5단계와 일부 병렬). 7단계(배포)와 8단계(운영과 회고)는 하지 않는다. 마감은 `TASKS.md`를 따른다(2026-11-06 13:30. 2026-11-06 09:45에 17:00에서 당겨졌다). 6단계 사전 점검은 5단계와 병렬로 다른 세션이 했다(2026-11-06 10:00 사용자 정정). 6단계 도구 사용 방식은 6행 이유 열에 있다. 7, 8단계 디렉토리는 2026-11-05에 지웠다. 8단계의 회고 역할은 단계마다 끝에 하는 회고(`retro`)가 대신한다.
- 기본: 처음에는 **superpowers 하나**로 시작하려 했다. 3단계(구현)는 superpowers를 설치하지 않고 구현 스킬 없이 진행했다. 작업 순서는 TASKS.md, 진행은 프로젝트 내장 stage 스킬 run 모드다. TDD는 `CLAUDE.md` 작업 규칙으로 지켰다. 병렬은 격리 worktree 서브에이전트로 했다. 격리 worktree는 기본 브랜치에서 갈라지므로 워커는 코디네이터 HEAD로 맞춘 뒤 시작한다. superpowers와 비교한 근거는 없다.
- 요구가 불명확할 때만 ouroboros `interview`를 한 번 쓴다.
- 프롬프트나 그래프 구조를 비교할 때만 pstack `/arena`를 쓴다.
- gstack은 Windows 마찰과 배포 중심 성격 때문에, gajae-code는 무인 장시간 작업용이라 지금은 쓰지 않는다.
- 계획 단계를 가진 도구가 gstack, superpowers, ouroboros 셋이다. 겹쳐 쓰면 트리거가 충돌하고 컨텍스트가 늘어나므로 하나만 고른다.
- paperthin은 개발 방법론이 아니라 산출물 품질 보조 스킬 모음이다. superpowers와 역할이 겹치지 않으므로 필요한 스킬만 골라 얹는다. 처음에는 `readchk`, `factchk`, `re0`, `ssotize` 정도면 충분하다. `re0-plan`, `re0-loop`는 계획 도구와 겹치므로 쓰지 않는다.
- `readchk`는 요구사항 단계에 둔다. 3단계 계획에는 넣지 않는다. 3단계는 TASKS.md 작업마다 `확인:` 줄이 있어 지시 해석의 갈림길이 작았다. 03 계획에 넣었지만 호출 기록이 없고, 02 단계 두 번 호출에서도 갈림길을 올리지 않았다.
- 보조 스킬을 계획에 넣으면 기록 파일에 호출 줄을 남긴다. 남기지 않으면 회고에서 평가할 수 없다.
- 실험·평가 단계는 `mandela`를 모델 호출 전, 실험·평가 설계에 한 번 돌린다. 점검은 설계자가 아닌 맥락 없는 서브에이전트가 한다. 결과 뒤 점검은 해석용으로 한 번 더 한다. 04에서 결과 뒤 점검이 찾은 위협 3개는 호출 전에 고칠 수 있었다. 05에서 평가 전 점검은 계획에 없던 누수 3개를 찾았고, 그 보완안(사례 표)에서 발견 하나가 나왔다.
- 근거를 공식 문서로 제한하므로 `docs-langchain`, `reference-langchain` MCP로 페이지 허용 목록과 스냅샷을 만든다. 스냅샷은 앱 코드에서 Python MCP 클라이언트로 받는다. 30KB 출력 한도는 줄 범위 분할과 서버 sha256 대조로 넘는다. 호출마다 시간 제한을 둔다(60초, 재시도 3회).
- paperthin 스킬 상당수(`re0`, `readchk`, `aim`, `nba`, `ssotize` 등)는 이 환경에 이미 설치되어 있다. 새로 설치하기 전에 `npx skills` 설치본과 중복되는지 확인한다.

## 이 도구들이 덮지 못하는 영역 (앱 자체의 품질)

위 도구는 개발 프로세스 도구다. LLM 앱 고유의 영역은 별도로 필요하다.

- 프롬프트와 출력 평가 데이터셋 (Langfuse 데이터셋과 eval)
- 트레이싱과 관측: 호출별 비용, 지연, 오류 (Langfuse Cloud 무료 티어 기준, 아래 한도 참고)
- 모델이나 프롬프트 변경 시 회귀 테스트
- 비용 제한, 레이트리밋, 프롬프트 인젝션 방어. Bedrock 일일 토큰 한도(`Too many tokens per day`)는 소스 리전과 추론 프로필마다 따로 걸린다. 대량 생성 전에 전환 순서를 정한다.
- 실험 배치는 운영과 겹치지 않는 배치 ID와 Langfuse 태그를 쓴다. 겹치면 실험 사용량을 운영과 나누지 못한다.
- 문서 원문을 입력에 넣는 호출은 첫 실행 실측으로 비용을 다시 잡는다. 04 Judge 호출은 4자당 1토큰 추정보다 입력이 37% 많았다.
- 모델이 만든 코드를 실행하는 샌드박스는 구현 단계 끝에 탈출 시도로 확인한다. 같은 프로세스 안 패치는 격리가 아니다. 03이 기술 부채로 넘긴 `_socket` 우회가 05에서 `.env` 반출로 재현됐다.

ouroboros `evaluate`는 코드의 수용 기준을 검증하는 것이지, 앱이 내는 응답 품질을 측정하지 않는다.

## Langfuse Cloud 무료 티어 (Hobby) 한도

출처: https://langfuse.com/pricing (2026-11-04 확인). 요금제는 바뀔 수 있으니 사용 전에 다시 확인한다.

| 항목 | 한도 |
|---|---|
| 사용량 | 월 50k units (추가 사용 옵션 없음) |
| 데이터 보관 | 30일 |
| 사용자 / 프로젝트 | 2명 / 무제한 |
| 어노테이션 큐 / 알림 | 1개 / 2개 |
| 수집 처리량 | 분당 1,000 요청 |
| API 제한 | 일반 분당 30, Datasets 분당 100, Observations v2 분당 30, Metrics v2 일 100 |
| 지원 | GitHub 커뮤니티 |

- 신용카드 없이 시작한다. 로컬 Docker 없이 쓸 수 있고, SDK와 연동은 셀프호스트와 동일하게 동작한다고 공식 문서에 적혀 있다.
- 한도 초과 시 동작(수집 중단 여부 등)은 확인하지 못했다. 가입 후 사용량 화면과 문서를 직접 확인한다.
- "unit"의 정의는 가격 페이지에서 확인하지 못했다. 일반적으로 트레이스, observation, score를 합친 수로 알려져 있으나 미검증이다. LangGraph는 노드마다 observation이 생기므로 한 번 호출에 unit이 여러 개 소모될 수 있다. 첫 실행 후 호출 1회당 소모량을 측정해 둔다.
- 30일 보관 제한 때문에 장기 기준선은 Langfuse에만 의존하지 않는다. 평가 데이터셋(질문, 기대 답)과 기준선 점수는 저장소에 파일로도 남긴다.
- API 호출 제한(특히 분당 30)이 낮다. 데이터셋 eval 스크립트에서 Observations API를 반복 조회하지 않는다.
- 월 50k를 넘기면 유료 Core(월 $29, 100k units 포함, 추가 100k당 $8)로 올리거나, 트레이스 샘플링 또는 셀프호스트를 고려한다. 셀프호스트는 이 PC의 여유 RAM이 약 4GB(총 15.9GB)라 빠듯할 수 있다.

## 진행 순서

1. superpowers `brainstorming`으로 범위와 성공 기준을 정한다.
2. Langfuse Cloud 무료 계정을 만들고, LangGraph 최소 그래프에 첫 호출부터 트레이스를 붙인다.
3. 호출 1회당 unit 소모량을 측정해 월 50k 안에서 가능한 실행 횟수를 계산한다.
4. 대표 질문 10~20개로 Langfuse 데이터셋을 만들고 eval 기준선을 잡는다. 데이터셋과 점수는 파일로도 보관한다.
5. 프롬프트나 모델을 바꿀 때마다 데이터셋으로 회귀를 확인한다. 데이터셋 실행도 unit을 쓰므로 횟수를 아낀다.

콜백 핸들러 API는 버전마다 바뀌므로, 구현 전에 공식 문서를 확인한다. 로컬 Docker Compose 셀프호스트는 무료 한도를 넘거나 데이터 보관 제한이 문제일 때의 대안으로 둔다.

## 참고 링크

- gstack: https://github.com/garrytan/gstack
- superpowers: https://github.com/obra/superpowers
- ouroboros: https://github.com/Q00/ouroboros
- gajae-code: https://github.com/Yeachan-Heo/gajae-code
- pstack: https://github.com/cursor/plugins/tree/main/pstack
- paperthin: https://github.com/LilMGenius/paperthin
- Langfuse 요금제: https://langfuse.com/pricing
