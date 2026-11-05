# 03 구현 단계 실행 계획

상태: 승인 (2026-11-05). 결정 1은 추천안(superpowers 설치 안 함)으로 확정
작성일: 2026-11-05
수정: 2026-11-05, 사용자 지시로 마감을 2026-11-06 17:00으로 당겼다. 상위 문서(requirements 2.0, seed 1.1.0, SERVICE.md 0.4)를 함께 고쳤다. 변형 문제(T7.1)를 면제하고 체크포인트를 2026-11-06 09:00으로 옮겼다. 일정은 [TASKS.md](../../TASKS.md) "일정" 절에 있다
대상: [SERVICE.md](../../SERVICE.md), [design.md](../02-spec-design/output/design.md), [seed.yaml](../02-spec-design/output/seed.yaml), [page-allowlist.md](../02-spec-design/output/page-allowlist.md), [06-output.md](02-spec-design/06-output.md). 2단계 확정 산출물 3개와 PRD 1개
근거: [skillset-by-lifecycle.md](skillset-by-lifecycle.md)의 "3. 구현" 행. 도구 README는 2026-11-05에 다시 읽지 않았다(미확인). 02 계획의 2026-11-04 확인을 따른다.

## 1. 목표

- **입력**: 위 "대상" 파일. 링크는 [input/README.md](../03-implementation/input/README.md)에 있다.
- **작업 순서**: [TASKS.md](../../TASKS.md). 묶음 M0~M7, 작업 48개(T7.1 면제로 47개). 작업마다 30분~1시간이고 `확인:` 줄이 하나씩 있다.
- **산출물**:
  - 코드: `app/`, `sandbox/`, `web/`, `packs/langchain/`, `data/`(design.md 4.1). `docs/` 밖에 둔다.
  - `docs/03-implementation/output/`: 코드 경로와 검증 결과 요약만 둔다. 예: `m0-smoke.md`(T0.13), 완료 조건 점검표(T6.3).
- **최종 문서**: `docs/03-implementation/output/<파일>`. 파일 이름과 장 구성은 `.claude/skills/stage/templates/output-types.md`의 03 행을 `doc` 모드에서 확인한다.
- **부산물**: 묶음별 수행 기록. `docs/dev-process/03-implementation/`에 둔다.
- **닫아야 할 결정**:
  1. superpowers 설치 여부: **설치 안 함으로 확정(2026-11-05, 사용자 선택)**. 추천은 설치하지 않는 것이었다. 이유: 마감까지 2일, 스킬 자동 발동의 트리거 충돌, `writing-plans`가 TASKS.md와 겹친다. 설치하지 않으면 TDD 규율은 "테스트를 먼저 쓰고 실패를 본 뒤 구현"으로 직접 지킨다.
  2. 스냅샷 수집 방법(T0.3). 후보는 design.md 4.3의 둘이다. 30KB 출력 한도를 넘는 페이지의 분할 읽기도 함께 정한다.
  3. 앱 Python·`langchain`·`langgraph` 버전(T0.1). 교안 `sds-ax-practice`(`20df7f6`)에서 확인한다.
  4. M0 임시 규칙("풀이 10개 미만이면 있는 만큼 낸다", T0.10)을 T4.2에서 없앤다.

## 2. 도구별 역할

| 도구 | 역할 | 입력 | 출력 | 이 환경 상태 |
| --- | --- | --- | --- | --- |
| superpowers (TDD, worktree, subagent) | 1순위. 구현 규율 | TASKS.md 작업 | 코드, 테스트 | 미설치(`~/.claude/plugins/installed_plugins.json`, `~/.claude/skills/` 확인, 2026-11-05). 결정 1 |
| `docs-langchain` MCP | 허용 목록 페이지 스냅샷 수집(T0.3, T1.5, T1.6) | `page-allowlist.md` 경로 | `packs/langchain/snapshots/*.mdx` | 연결 확인(2026-11-05, `query_docs_filesystem_docs_by_lang_chain`의 `wc -c` 응답) |
| `reference-langchain` MCP | API 레퍼런스 스냅샷 수집(T1.6) | `page-allowlist.md`의 api-ref 행 | `get_symbol` 출력 텍스트 | 도구 목록에 있음. 호출 확인은 T1.6에서 한다(미확인) |
| paperthin `readchk` | 묶음 지시를 맞게 읽었는지 검증 | 묶음 시작 지시 | 갈림길이 남을 때만 질문 | 설치됨(세션 스킬 목록, 2026-11-05) |

고르지 않은 도구:

- pstack `/tdd`, `/blast-radius`: 보조 도구다. 미설치(2026-11-05)다. 기존 코드가 없어 영향 범위 분석의 쓸모가 작다.
- ouroboros `run`(`ouroboros_start_execute_seed`): "이 프로젝트의 선택" 절은 계획 단계를 가진 도구를 하나만 쓰라고 한다. 작업 순서는 TASKS.md가 정한다. Seed 수용 기준 검증은 5단계 `evaluate`의 일이다.
- gstack, gajae-code: "이 프로젝트의 선택" 절이 제외했다.

도구 설명 요약:

- superpowers(02 계획, README 2026-11-04): 스킬이 자동 발동한다. 설치는 `/plugin install superpowers@claude-plugins-official`다. SessionStart 훅 동작은 미확인이다.
- `docs-langchain` MCP(도구 설명, 2026-11-05): 읽기 전용 가상 파일 시스템이다. 호출당 출력은 30KB에서 잘린다.

## 3. 진행 순서

### 0단계: 사전 준비

1. Bedrock 자격 증명과 `AWS_REGION`(`us-east-1`, `us-west-2`, `ap-northeast-2` 중 하나)을 준비한다. 서버와 샌드박스에는 넘기지 않는다.
2. 교안 저장소 `Lana-sds/sds-ax-practice`(`20df7f6`)에 접근할 수 있는지 확인한다.
3. 1장 결정 1~4를 닫는다.
4. 기록 파일마다 시작·완료 시각을 남긴다.

### K단계: TASKS.md 묶음 MK-1

각 단계는 TASKS.md의 묶음 하나다. 묶음 안 작업은 위에서부터 한다.

| 단계 | 묶음 | 끝나는 조건 | 기록 파일 |
| --- | --- | --- | --- |
| 1 | M0 최소 경로 | T0.13 확인 통과: 빈 DB에서 문서 순서대로 결과 화면까지 간다 | `01-m0.md` |
| 2 | M1 결정적 로직·근거 자료 | T1.6, T1.7 확인 통과 | `02-m1.md` |
| 3 | M2 파이프라인 | T2.7~T2.9 확인 통과 | `03-m2.md` |
| 4 | M3 파일럿·축소 판단 | T3.2 판단이 기록됨 | `04-m3.md` |
| 5 | M4 풀 배치·풀이 기능 | T4.1, T4.6 확인 통과 | `05-m4.md` |
| 6 | M5 풀 고정·감사 | T5.5 또는 T5.6 확인 통과 | `06-m5.md` |
| 7 | M6 완료 조건 | T6.3 점검표가 있다 | `07-m6.md` |
| 8 | M7 축소 대상 | T7.2 확인 통과 또는 면제 기록. T7.1은 면제 | `08-m7.md` |

기록 파일 이름은 템플릿의 `0K-<도구>.md` 대신 묶음 이름을 쓴다. 모든 단계가 같은 방식으로 진행되기 때문이다.

## 4. 사전 조건과 위험

| 항목 | 내용 | 대응 |
| --- | --- | --- |
| 일정 | 마감 2026-11-06 17:00. 2026-11-05 09:10 기준 남은 시간은 약 32시간이다. 작업 47개는 작업당 30분이어도 약 24시간이다 | TASKS.md "일정" 절의 목표 시각을 따른다. 2026-11-06 09:00 체크포인트(T3.2)에서 SERVICE.md 7.2의 2, 3번을 판단한다 |
| superpowers 설치 영향 | 스킬이 자동 발동한다. 훅 동작은 미확인이다. `writing-plans`가 TASKS.md와 겹친다 | 결정 1. 설치하면 이 계획 상단에 "수정:" 줄을 남긴다 |
| MCP 출력 한도 | 호출당 30KB. 확인한 크기: `graph-api.mdx` 31,352B, `knowledge-base.mdx` 34,520B, `middleware/built-in.mdx` 74,351B, `workflows-agents.mdx` 49,426B(2026-11-05) | T0.3에서 분할 읽기와 바이트 수 대조로 확인한다 |
| `.python-version` | `.gitignore`에 있다. US-0.1은 이 파일 고정을 요구한다 | T0.1에서 `.gitignore` 줄을 뺀다 |
| Bedrock 자격 증명 | 생성 배치에만 필요하다. 준비되지 않으면 T0.5부터 막힌다 | 0단계 1 |
| Bedrock 단가 | 미확인 | T2.8에서 AWS 가격 페이지로 채운다. 없으면 `cost_usd`는 NULL이다 |
| 교안 버전 | 앱 Python·`langchain`·`langgraph` 버전이 미확인이다 | T0.1. 확인하지 못하면 lock 시점 최신으로 고정하고 기록한다 |

## 5. 기록과 평가

기록 위치는 `docs/dev-process/03-implementation/`이다.

| 파일 | 내용 |
| --- | --- |
| `01-m0.md`~`08-m7.md` | 묶음별 결정, 계획과 다른 점, 확인 결과 |
| `09-retro.md` | 도구별 평가 |

평가 기준은 `.claude/skills/stage/templates/retro.md`를 따른다. 이 단계에서 추가하는 기준:

- 작업별 실제 걸린 시간과 30분~1시간 기준의 차이
- 확인 줄이 처음 시도에 통과한 작업 수
- `modelchk` 권고 등급(06-output.md)이 실제 사용 등급과 맞았는지
