# LLM 앱 개발 라이프사이클별 스킬셋 추천

작성일: 2026-11-03
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

| 단계 | 1순위 | 보조 | 이유 |
|---|---|---|---|
| 1. 아이디어와 요구사항 | gstack `/office-hours` | ouroboros `interview`, paperthin `aim`, `readchk` | gstack은 프레이밍을 도전하고, ouroboros는 모호성을 점수로 막는다. paperthin은 데이터나 지시를 받았을 때 의도를 제안하고 이해를 검증한다. |
| 2. 스펙과 설계 | ouroboros `seed` | superpowers `brainstorming`, `writing-plans`, paperthin `re0-plan`, `modelchk` | 수용 기준을 Seed로 고정한다. 가볍게 가려면 superpowers만 쓴다. `modelchk`는 작업에 맞는 모델 등급과 추론 강도를 정한다. |
| 3. 구현 | superpowers (TDD, worktree, subagent) | pstack `/tdd`, `/blast-radius` | 규율은 superpowers가 자동으로 강제하고, 영향 범위 분석은 pstack이 낫다. |
| 4. 프롬프트와 모델 실험 | pstack `/arena` | ouroboros `evolve` | 변형 N개를 시도해 최선을 합친다. |
| 5. 평가와 리뷰 | ouroboros `evaluate` | pstack `/interrogate`, gstack `/review`, paperthin `mandela`, `factchk`, `shower`, `sip` | 기준 충족 증명, 다중 모델 적대적 리뷰, 프로덕션 버그 탐지. paperthin은 평가 누수 점검(`mandela`), 사실 검증(`factchk`), 무맥락 재독(`shower`), 작성 직후 자가 점검(`sip`)을 더한다. |
| 6. QA | gstack `/qa` | superpowers 검증 스킬 | 실제 브라우저에서 버그를 재현하고 고친다. UI가 있는 앱에 유용하다. |
| 7. 배포 | gstack `/ship`, `/canary` | pstack ship 플레이북, paperthin `re0-merge`, `re0-release` | PR 생성과 배포 후 모니터링. |
| 8. 운영과 회고 | gstack `/retro`, `/cso` | pstack `/reflect`, `/correct`, paperthin `re0-memo`, `ssotize`, `catchup` | 회고와 보안 감사. paperthin은 교훈 정리, 문서 중복 통합, 공백 후 맥락 복구를 맡는다. |
| 문서와 산출물 정리 (전 단계 공통) | paperthin `re0`, `debloat`, `ssotize` | paperthin `detool`, `dedash`, `reorder` | 반복 작업 후 산출물을 최신 v0로 정리하고, 흩어진 사실을 한 곳으로 모은다. |
| 장시간 무인 작업 | gajae-code | ouroboros `ralph`, pstack 야간 실행 플레이북, paperthin `re0-loop`, `nba` | 원격 승인과 구독 재활용이 필요할 때. `re0-loop`는 build, QA, 회고를 반복하고 `nba`는 다음 행동 하나를 고른다. |

## 이 프로젝트(로컬 미니 프로젝트)의 선택

- 기본: **superpowers 하나**로 시작한다.
- 요구가 불명확할 때만 ouroboros `interview`를 한 번 쓴다.
- 프롬프트나 그래프 구조를 비교할 때만 pstack `/arena`를 쓴다.
- gstack은 Windows 마찰과 배포 중심 성격 때문에, gajae-code는 무인 장시간 작업용이라 지금은 쓰지 않는다.
- 계획 단계를 가진 도구가 gstack, superpowers, ouroboros 셋이다. 겹쳐 쓰면 트리거가 충돌하고 컨텍스트가 늘어나므로 하나만 고른다.
- paperthin은 개발 방법론이 아니라 산출물 품질 보조 스킬 모음이다. superpowers와 역할이 겹치지 않으므로 필요한 스킬만 골라 얹는다. 처음에는 `readchk`, `factchk`, `re0`, `ssotize` 정도면 충분하다. `re0-plan`, `re0-loop`는 계획 도구와 겹치므로 쓰지 않는다.
- paperthin 스킬 상당수(`re0`, `readchk`, `aim`, `nba`, `ssotize` 등)는 이 환경에 이미 설치되어 있다. 새로 설치하기 전에 `npx skills` 설치본과 중복되는지 확인한다.

## 이 도구들이 덮지 못하는 영역 (앱 자체의 품질)

위 도구는 개발 프로세스 도구다. LLM 앱 고유의 영역은 별도로 필요하다.

- 프롬프트와 출력 평가 데이터셋 (Langfuse 데이터셋과 eval)
- 트레이싱과 관측: 호출별 비용, 지연, 오류 (Langfuse Cloud 무료 티어 기준, 아래 한도 참고)
- 모델이나 프롬프트 변경 시 회귀 테스트
- 비용 제한, 레이트리밋, 프롬프트 인젝션 방어

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
