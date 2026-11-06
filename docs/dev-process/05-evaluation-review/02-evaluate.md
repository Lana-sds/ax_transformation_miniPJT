# 02 evaluate 기록

상태: 진행 중
시작: 2026-11-06 09:22
완료:
계획: [05-evaluation-review-plan.md](../05-evaluation-review-plan.md)의 2단계(상단 "수정:" 줄 P1, P2, P3, P6 반영)
세션 모델: Opus 5.5(`claude-opus-5-5`). 추론 강도: 미확인

## 입력

- Seed 1.1.0: goal, 주요 constraints, 수용 기준 9개 원문을 `seed_content`로 넘겼다. 13 KB 전문 대신 goal, constraints 13줄(요약 아님, 원문 발췌), acceptance_criteria를 넘겼다. ontology와 평가 원칙 절은 넘기지 않았다
- `acceptance_criteria`: 9개 원문
- `artifact`: 아래 증거 E0~E4의 원본 출력 핵심 줄(P6). 스크래치 `ev/artifact.md`가 전문이다
- `working_dir`: 스크래치 `eval-src`(P1). `git archive 3a48c4cb`에서 `docs/`, `TASKS.md`, `.claude/`를 뺐다. 코드가 읽는 `docs/02-spec-design/output/page-allowlist.md` 한 파일만 더했다(없으면 테스트 17개가 `FileNotFoundError`). 03 판정 문서(`implementation.md`, `mvp-checklist.md`)는 없다
- `auto_evolve: false`(결정 4), `trigger_consensus: false`(결정 5), `session_id: eval-05-20261106`

### `.ouroboros/mechanical.toml`(평가 사본에만 둠)

```toml
test = "uv run --directory app pytest -q"
lint = "npm --prefix web run lint"
build = "npm --prefix web run build"
coverage_threshold = 0.0
timeout = 600
```

- 명령마다 ouroboros 0.59.9 `detector._command_is_valid`로 미리 검사했다(`uvx --from ouroboros-ai==0.59.9`). 셋 다 `True`
- `coverage_threshold = 0.0`: 요구사항에 커버리지 기준이 없다. 켜 두면 커버리지 명령이 없을 때 승인이 막힌다(evaluation-pipeline.md). 커버리지는 이월 항목에서 따로 잰다
- 평가 사본에서 `uv sync`(app, sandbox), `npm ci` 뒤 `uv run --directory app pytest -q`: 374 passed

## 진행

### 증거 수집(2026-11-06 09:25~09:40)

| ID | 무엇 | 방법 | 결과 요약 |
| --- | --- | --- | --- |
| E0 | 전체 검사 | 0단계 결과, 기준 관련 테스트 파일 7개 | 374 passed. build·lint 종료 0. 관련 테스트 83 passed |
| E1 | 기준 1, 2, 3 DB 값과 P2 독립 재계산 | 스크래치 `ev/e01_pool.py`. 앱 패키지를 import하지 않는다. `mode=ro` | 풀 60, 버킷 10씩, 형식 code 11·multi 14·short 17·single 18. 저장값 quote_match 60·mapping 60·exec 11/11. 독립 재계산: 스냅샷 81개 sha256 불일치 0, 인용 불일치 0, 30자 미만 0, 허용 목록 밖 0, 매핑 무효 0. 버린 이유 없는 비passed 2개는 `audit_failed` 2개. 감사 `pass`(0, 0, 1, 20). 10행 세트 3개, 그 안 태그 없는 오답 0. 풀 전체로는 1(`s010` attempt 41) |
| E2 | 기준 1 코드형(P2) | 스크래치 `ev/e02_code.py`. 샌드박스 Python과 `runner.py`를 직접 부름 | 11문항 44보기, 실행≠기대값 0, 실행≠Judge 예측 0 |
| E3 | 기준 4, 5, 6, 7 API와 P3 사례 표 | 스크래치 `ev/e03_api.py`. 운영 DB 사본에 TestClient. 복습 큐는 임시 DB | 아래 |
| E4 | 공격자 발견 중 기준 관련 재현 | [03-interrogate.md](03-interrogate.md) 검증 표 | B-1, B-4, C-1, C-2, C-4, A-6 등 |

E3 결과:

- 사본의 최신 세트 `s010`에 태그 없는 오답이 있어 `POST /api/sets`가 `409 untagged_wrong`. 사본에서만 태그한 뒤 세트 생성: 10문제, 모두 현재 풀
- 답 전 공개 필드 `bucket, choices, format, question_id, review, select_count, stem_en`. 금지 키 0. 해설·인용 문자열이 응답 어디에도 없음. `GET` 결과 `{}`
- 답 뒤 `answer_key, explanation_ko, segments(ko 포함), grounding(quote, url), doc_url` 등. 다른 문제 결과는 여전히 없음
- 풀 코드형 11개의 `doc_url`이 모두 `https://docs.langchain.com/` 또는 `https://reference.langchain.com/`

### P3 사례 표

맥락 없는 서브에이전트(general-purpose)가 `seed.yaml`, `requirements.md`만 읽고 썼다(코드·테스트·03 이후 문서 읽기 금지, 도구 호출 3회). 40행이다. 결정된 사례는 서버와 같은 경로(`grading.normalize_answer` → `grading.grade`)와 API로 돌렸다.

| 묶음 | 사례 | 결과 |
| --- | --- | --- |
| 채점 결정(24) | K-1~K-4, K-6~K-8, K-9 빈 선택, K-10~K-16, K-20, K-21 키릴, K-22, K-23 | 불일치 0 |
| 채점 spec silent(7) | K-5 순서만 다른 복수 선택 → 정답. K-9 중복 선택 → 오답. K-17 `add_node()()` → 오답. K-18 따옴표 → 오답. K-19 `add _node` → 정답. K-21 전각 → 정답, NBSP → 정답 | 판정 근거로 쓰지 않는다(작성자 메모 5) |
| 노출(K-25~K-29) | E3 | 일치. K-28(오답 때 정답 키 공개)은 spec silent. 앱은 공개한다 |
| 세트(K-30, K-31) | 임시 DB 15세트 | 복습 최대 3 유지(세트 3에 3개, 넘친 1개는 세트 4로). 새 문제 소진 뒤에도 세트가 이어짐 |
| 복습 큐(K-32~K-38) | 임시 DB, API | X(독해) 오답→4(세트 3이 꽉 차 밀림)→오답→9→오답→다시 안 나옴. Y 오답→3 정답→빠짐. Z(개념, 변형 V 있음)→V가 3에 나옴, Z는 안 나옴. W(개념, 변형 없음)→3 오답→8 오답→빠짐 |
| K-39, K-40 | 태그가 바뀐 2차 복습, 같은 문제 재제출 | spec silent. 재제출은 409 `already_answered`(공격자 B 확인) |

사례 작성자가 짚은 문서 차이: requirements FR-3.2는 대소문자와 공백만 정규화한다고 쓰고, seed 기준 6은 백틱과 끝 `()`까지 쓴다. seed 머리말은 둘이 다르면 requirements를 따르라고 한다. 앱은 seed와 design.md 4.4를 따른다. 5단계 발견 후보다.

## 인계

갱신: 2026-11-06 09:45
- 마지막 완료 작업: 증거 E0~E4 수집, `ouroboros_start_evaluate` 호출
- 다음 작업: 작업 결과를 받아 기준별 판정을 `acceptance.md`에 옮긴다. `chained_ralph_job_id`가 있으면 바로 취소한다
- 실행 중: ouroboros 평가 `job_a0459ed89d34`(session `eval-05-20261106`)
- 사용자 대기: 없음
- 먼저 읽을 파일: 이 파일, 스크래치 `ev/artifact.md`

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 평가 사본에 `page-allowlist.md` 포함 | 코드(`allowlist.py` 20행, `slots.py` 31행)가 읽는 입력 파일이다. 판정 문서가 아니다 | 없음(P1 범위 안) |
| seed 발췌 전달 | goal, constraints 원문 발췌, 수용 기준 9개. ontology 절은 뺐다 | 계획 2단계 3번 "seed.yaml 원문" |

## 계획과 다른 점

- `working_dir`가 worktree 루트가 아니라 `docs/` 없는 사본이다(P1)
- `seed_content`가 전문이 아니라 발췌다(위 "결정")
- 기준 4, 6, 7 증거에 P3 사례 표 실행을 더했다

## 끝나는 조건 확인

- 조건: 9개 기준과 MVP 완료 조건 4개가 `acceptance.md`에 `통과`, `실패`, `미확인` 중 하나로 있다. 1단계 기계 검사가 하나 이상 돌았다.
- 결과: 미확인(진행 중)
