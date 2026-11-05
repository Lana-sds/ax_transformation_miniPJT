# 3 ouroboros `seed` 기록

상태: 완료
시작: 2026-11-04 14:55
완료: 2026-11-04 15:04
계획: [02-spec-design-plan.md](../02-spec-design-plan.md)의 3단계

## 입력

- 경로: `session_context`(계획 결정 2)
- 지시: "bedrock-model-list.md 업데이트 했어. 3단계 진행하자"
- 입력 변경: 사용자가 `bedrock-model-list.md`를 고쳤다(작업 트리 변경, 커밋 전). 리전 3개(us-east-1, us-west-2, ap-northeast-2)별 목록이 됐고 `nova-micro`, `openai.gpt-oss-*`(us-east-1만)이 더해졌다.
  - NFR-4 모델 3개(`global.anthropic.*`)는 세 리전 모두에 있다. 모델 결정은 바뀌지 않는다.
  - `openai.gpt-oss-*`는 `CLAUDE.md` 고정 결정("Claude, Amazon Nova")에 없어 쓰지 않는다.
  - 리전은 정하지 않았다. 환경 변수로 받고 세 리전 중 하나로 둔다는 제약으로 Seed에 넣는다.

## 진행

### 생성

- `ouroboros_generate_seed(session_context)` 1회 호출. `gap_questions_required` 없이 바로 생성됐다.
- 넘긴 값: `goal` 1개(requirements 1.1 원문), `acceptance_criteria` 12개, `constraints` 10개, `decisions` 8개, `project_type: greenfield`
- 결과: `seed_2628c03dc62f`, 모호성 0.20(서버 표시 "conservative ceiling — gate was structural, not scored"). `decisions`는 `constraints`에 합쳐져 제약 18개가 됐다.
- 서버가 만든 부분: `ontology_schema`는 `SessionSettledContract`, `fields: []`(빈 목록). `evaluation_principles`와 `exit_conditions`는 일반 문구 1개씩이다.
- 저장 위치: `~/.ouroboros/seeds/`는 비어 있다. 이 worktree에 `.ouroboros/`가 생기지 않았다. 도구는 YAML을 응답으로만 돌려줬다. `output/seed.yaml`에 응답 원문을 쓰고 상단에 주석 2줄만 붙였다.

### QA 자문 (1회)

- `ouroboros_qa`, 기준 0.90, 세션 `qa-dbc61866`
- 판정: REVISE, 점수 0.50. Correctness 0.55, Completeness 0.45, Quality 0.60, Intent Alignment 0.70, Domain Specific 0.35
- 주요 지적:
  1. 온톨로지가 비었다. Question, PoolSnapshot, Attempt, ReviewItem, AuditRecord 같은 개체가 없다.
  2. 수단형 기준이 섞였다. 결정적 게이트는 풀 기준의 "통과" 정의에 속한다. 파이프라인 실행·SQLite 저장·Langfuse·지표 파일 기준은 결과가 아니라 수단이다.
  3. 측정 도구가 없는 기준이 있다. 3세트 풀이와 태그는 조회 조건이 없다. 지표 파일은 경로와 필드가 없다. 매핑 충실도는 판단 기준표가 없다.
  4. 모순이 있다.
     - 목표의 day2~day7과 버킷 6개의 대응이 없다.
     - 축소 규칙(변형 문제, Langfuse 내보내기 제외, 30문제)이 해당 기준과 충돌한다.
     - MCP 코드형을 뺀 뒤에도 코드 선택 형식 10개를 채울 수 있는지 명시가 없다.
  5. 모호한 제약이 있다.
     - "문서 최신 버전"
     - 6세트 후 채우는 순서
     - Bedrock·샌드박스 타임아웃 없음
     - 배치 재개와 멱등성 없음

### 질문과 답

| 질문 | 선택지 | 답 |
| --- | --- | --- |
| QA REVISE 뒤 Seed 처리 | 직접 편집(추천) / 개선 패스(lateral 5개) / 그대로 둠 | 직접 편집 |
| GitHub star | Not now / Star | Not now. `~/.ouroboros/prefs.json`에 `star_asked: true`를 기록했다(파일이 없어 새로 만들었다). `gh api`는 실행하지 않았다 |

### 직접 편집 (v1.0.0 → v1.0.1)

생성은 다시 부르지 않았다(스킬 규칙: 재생성 시 온톨로지를 버린다). QA 1차 지적을 받아 YAML을 고쳤다.

| 구분 | 변경 |
| --- | --- |
| 온톨로지 | `fields: []`를 개체 11개로 채웠다. Question, Segment, GroundingRecord, AllowlistPage, VerificationResult, Batch, PoolSnapshot, QuizSet, Attempt, ReviewItem, AuditRecord. 필드 이름은 requirements FR-8, FR-10, GR-3을 따랐다 |
| 수용 기준 12개 → 9개 | 결정적 게이트(옛 2번)와 배치·버린 이유(옛 10번)를 풀 기준(1번)에 합쳤다. SQLite 저장(옛 9번)을 3세트 기준(3번)에 합치고 "서버 재시작 후 SQLite 조회"로 확인하게 했다 |
| 측정 가능하게 | 3세트: set_id 3개 × 10개 기록, 오답 중 태그 빈 행 0, 독해 실수 행에 segment_id. 감사: SQLite 문항별 기록, 매핑 불충실의 판단 기준(한 segment라도 뜻을 빠뜨리거나 덧붙임). Langfuse: 환경 변수 없이 오류 없음, 있으면 배치 trace 1개 이상 |
| 모순 해소 | day→버킷 대응을 제약에 넣었다. 축소 규칙을 제약에서 빼고 조건부 완료 `scope_cut_waiver`로 옮겼다. 코드 선택 10개는 MCP를 뺀 주제에서 채운다고 적었다 |
| 표현 정리 | "6세트 후"를 "새 문제가 소진되면(약 6세트 후)"로, "5세트 뒤에도 틀리면"을 "두 번째 복습에서도 틀리면"으로 바꿨다. "문서 최신 버전"을 "lock 시점의 최신 릴리스로 고정"으로 바꿨다. 감사 재감사 절차는 제약으로 옮겼다 |
| 받지 않은 지적 | 모델 ID, 고정 버전, MVP 밖 목록을 제약에서 빼라는 지적은 받지 않았다. 사용자가 확정한 고정 결정이다. 타임아웃·배치 재개·멱등성 값은 Seed에서 새로 정하지 않고 `design.md`로 넘겼다 |

YAML 파싱 확인: 제약 20, 수용 기준 9, 온톨로지 개체 11, 완료 조건 2(`uv run --with pyyaml`, 15:01).

### QA 자문 2차 (편집 확인용 1회)

- 같은 세션 `qa-dbc61866`, 1차 결과와 반영·거절 목록을 `iteration_history`로 넘겼다.
- 판정: REVISE, 0.50 → 0.72. Correctness 0.75, Completeness 0.78, Quality 0.62, Intent Alignment 0.75, Domain Specific 0.72
- 남은 지적:
  1. 기준이 겹친다. 세트 출제(4번)와 복습 큐(7번), 풀이 화면(5번)과 채점(6번)이다.
  2. 풀 기준(1번)에 과정이 섞였다. "Judge=실행", "버린 이유 기록"이다.
  3. 면제 조건이 수용 기준 문구와 충돌한다. 기준에 "면제 기록이 있으면 예외"가 없다.
  4. 지표 파일 경로와 비용 단가표를 `design.md`에 미뤘다.
  5. 모호한 제약이 있다. "배포를 막지 않게", "CCA-F 팩 분리", "근접 주제 규칙", "확장 가능"이다.
  6. 온톨로지에 개체가 빠졌다. Metrics, LangfuseTrace, UserWaiver가 없다. `mistake_tag` 빈 값은 정답일 때만 허용한다는 조건도 없다.
- 스킬 규칙상 개선을 이어가려면 사용자가 다시 선택해야 한다. 자동으로 고치지 않았다.

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| Seed 입력 경로 | `session_context` | 없음(계획 결정 2) |
| 리전 | 환경 변수, us-east-1·us-west-2·ap-northeast-2 중 하나 | 새 제약. 모델 목록 변경 반영 |
| 축소 규칙 | 조건부 완료로 표현. 면제 기록이 있어야만 이 조건으로 끝낸다 | 없음(requirements 1.6과 같은 내용) |
| Seed 수정 방식 | 개선 패스 대신 직접 편집 | 없음 |

### 직접 편집 (v1.0.1 → v1.1.0, 2026-11-05)

3단계 계획 중 사용자 지시로 고쳤다. 생성은 다시 부르지 않았다.

| 구분 | 변경 |
| --- | --- |
| goal | 마감 "2026-11-07까지"를 "2026-11-06 17:00까지"로 바꿨다 |
| `scope_cut_waiver` | 변형 문제를 체크포인트 전에 면제했다(사용자 선택: 축소 ①만 지금 적용). 체크포인트를 "2026-11-05 저녁"에서 "2026-11-06 09:00"으로 옮기고, 미달 시 Langfuse 내보내기 제외와 풀 30개 축소를 적용한다 |

## 계획과 다른 점

- 계획은 "개선 패스는 사용자가 원할 때만"이었다. 사용자는 개선 패스 대신 직접 편집을 골랐다. 편집 확인용으로 QA를 한 번 더 돌렸다(총 2회).
- 도구가 Seed를 파일로 저장하지 않았다(미확인 사항 확인). `output/seed.yaml`이 유일한 사본이다.

## 끝나는 조건 확인

- 조건: Seed YAML이 있고, QA 판정과 점수가 기록되었고, 사용자가 수용 기준 목록을 확인했다
- 결과: 충족. `output/seed.yaml` v1.0.1, QA 2회(0.50, 0.72 REVISE) 기록. 사용자가 수용 기준 9개를 그대로 확정했다(2026-11-04 15:04). 남은 QA 지적은 고치지 않고 위 2차 목록에 남긴다
