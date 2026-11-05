# TASKS: agent-dev-quiz 구현 순서

| 항목 | 내용 |
| --- | --- |
| 작성일 | 2026-11-05 |
| 기준 | [SERVICE.md](SERVICE.md) 0.5, [requirements.md](docs/01-requirements/output/requirements.md) 3.0, [design.md](docs/02-spec-design/output/design.md) 10.0, [seed.yaml](docs/02-spec-design/output/seed.yaml) 1.1.0 (2026-11-05 13:42 확인) |
| 단계 계획 | [03-implementation-plan.md](docs/dev-process/03-implementation-plan.md) |
| 마감 | 2026-11-06 17:00 (C-1) |

## 읽는 법

- 작업 하나는 30분~1시간이다. 넘치면 쪼갠다.
- `확인:` 줄이 통과하면 작업이 끝난다. 체크박스를 채운다.
- 괄호의 `US-`는 SERVICE.md 사용자 스토리, `W`는 설계 작업 단위([06-output.md](docs/dev-process/02-spec-design/06-output.md))다.
- 명령은 `app/`에서 `uv run ...`, `web/`에서 `npm ...`로 돈다.
- 새 요구사항을 더하지 않는다. "M0 임시"는 뒤 묶음에서 없앤다.

## 일정

오늘 2026-11-05 09:10 기준으로 남은 시간은 약 32시간이다. 작업 47개(M7 T7.1 면제)를 작업당 30분으로 잡아도 약 24시간이다. 시각은 목표다. 넘기면 체크포인트에서 축소를 판단한다. 그 뒤 사용자 요청으로 T2.10, T2.11, T4.7, T4.8, T4.9를 더해 작업은 52개다.

| 마일스톤 | 목표 시각 | 실제 | 상태 |
| --- | --- | --- | --- |
| M0 최소 경로 (T0.1~T0.13) | 2026-11-05 17:00 | 2026-11-05 09:41 | 완료 |
| M1 결정적 로직·스냅샷 (T1.1~T1.7) | 2026-11-05 20:00 | 2026-11-05 10:14 | 완료 |
| M2 파이프라인 (T2.1~T2.11) | 2026-11-05 24:00 | 2026-11-05 11:55 | 완료. 추가 작업 T2.10 crosscheck, T2.11 품질 기준 포함 |
| M3 파일럿·축소 판단 (T3.1, T3.2) | 2026-11-06 09:00 | 2026-11-05 13:42 | 완료. T3.1은 11:41. T3.2 판단은 60개 진행 |
| M4 풀 배치·풀이 UI (T4.1~T4.9) | 2026-11-06 12:00 | 2026-11-05 13:39 | 완료. `fill` 보충 9회. T4.8, T4.9는 끝나는 조건 밖이라 뒤에 끝냄(14:01) |
| M5 풀 고정·감사 (T5.1~T5.5) | 2026-11-06 14:30 | 2026-11-05 14:22 | 완료. 감사 `au_326384fb5422`가 `pass`다(14:19). T5.6 불필요 |
| M6 완료 조건 (T6.1~T6.3) | 2026-11-06 16:00 | 2026-11-05 14:50 | 완료. MVP 조건 4개 충족 |
| M7 (T7.2 Langfuse 내보내기) | 2026-11-06 17:00 | 2026-11-05 14:50 | 완료. T7.2 파일은 14:40. T7.1 변형 문제는 면제(`waivers.yaml`) |

"실제"는 마일스톤을 닫은 시각이다. 각 기록 파일(`docs/dev-process/03-implementation/0K-*.md`)의 "끝나는 조건 확인" 절과 커밋 시각에서 옮겼다.

- M4의 서버·UI 작업(T4.2~T4.6)은 풀 배치(T4.1)가 도는 동안 한다.
- 현황(2026-11-05 15:18): M0~M7 완료(T7.1 면제). 03 단계 최종 문서 [implementation.md](docs/03-implementation/output/implementation.md) 확정 1.0. 남은 일은 `retro`다. 최종 풀 `ps_326384fb5422`, 감사 `pass`, MVP 완료 조건 4개 충족.
- 스냅샷 수집(T1.5, T1.6)은 서로 독립이라 나눠 맡길 수 있다.

## M0 최소 경로: 스냅샷 1개 → 문제 1개 → 풀이 결과 화면

범위: 단일 선택 형식, LangGraph 기초 버킷 주제 1개(`/oss/python/langgraph/graph-api`), 생성→Judge→게이트 1회. 재생성, 샌드박스, 중복 검사, 복습, 태그, 백업은 뺀다.

- [x] T0.1 `app/` uv 프로젝트를 만든다. 교안 `sds-ax-practice`(`20df7f6`)에서 Python·`langchain`·`langgraph` 버전을 확인해 `.python-version`, `requires-python`, `uv.lock`에 고정한다. `.gitignore`의 `.python-version` 줄을 뺀다. FastAPI, uvicorn, `langchain-aws`, pytest(dev)를 넣는다 (US-0.1, W1)
  - 확인: `uv run python -c "import langchain, langgraph, fastapi, langchain_aws"`가 오류 없이 끝나고 `uv.lock`, `.python-version`이 `git status`에 보인다.
- [x] T0.2 `migrations/0001_init.sql`(설계서 5.1 전체), `db.py`, `migrate.py`, `quiz migrate` 명령을 만든다 (US-0.2, W1)
  - 확인: `uv run quiz migrate`를 두 번 돌려도 오류가 없고 `sqlite3 data/quiz.db ".tables"`가 5.1 테이블 13개를 모두 보인다.
- [x] T0.3 스냅샷 수집 방법을 정하고 `graph-api` 페이지 1개를 `packs/langchain/snapshots/oss__python__langgraph__graph-api.mdx`로 받는다. 30KB 한도를 넘는 페이지(이 페이지 31,352B)를 나눠 읽어 합치는 방법을 확인한다. 최소 `allowlist.yaml`(1행, `sha256`, `fetched_at`)을 손으로 쓴다 (US-1.1, W2)
  - 확인: 스냅샷 바이트 수가 MCP `wc -c` 값과 같고, `allowlist.yaml`의 `sha256`이 `sha256sum` 결과와 같다.
- [x] T0.4 `gates.py` 최소판: 인용 정규화(NFKC, 연속 공백 1칸), 인용 대조, 30자 이상, `page` 허용 목록 확인, `segments` 존재. 표준 라이브러리만 쓴다 (US-2.1, W3)
  - 확인: `uv run pytest tests/test_gates.py`가 규칙마다 통과·실패 사례 하나씩을 모두 통과한다.
- [x] T0.5 `llm.py` 최소판: `ChatBedrockConverse(region_name=..., config=...)` 생성 함수(adaptive 재시도 5회, 타임아웃 10/120초), 리전 3개 밖이면 오류 (US-2.5, W4)
  - 확인: 생성 모델과 Judge 모델에 짧은 프롬프트를 한 번씩 보내 응답 텍스트와 토큰 수가 출력되고, `AWS_REGION=eu-west-1`이면 시작 시 오류로 멈춘다.
- [x] T0.6 `generate` 노드: 단일 선택 구조화 출력 스키마(문제, 보기, 정답 키, 한국어 해설, `segments`, `grounding_records`)와 생성 프롬프트(`packs/langchain/prompts/`). 스냅샷 원문을 주고 `quote`를 그대로 복사하게 한다 (US-2.2, W6)
  - 확인: 노드를 단독 실행하면 스키마 검증을 통과한 문제 1개가 나오고 `gates.py`의 인용 대조를 통과한다.
- [x] T0.7 `judge` 노드와 LangGraph 그래프(generate → judge → gates, 재생성 없음) (US-2.2, W6)
  - 확인: 그래프를 1회 돌리면 Judge 판정 JSON과 게이트 결과가 함께 나오고 최종 판정이 `passed` 또는 실패 이유 하나다.
- [x] T0.8 `quiz generate --count 1` 명령: `batches`, `batch_slots`, `questions`, `grounding_records`, `verification_results`에 쓴다. `question_id`는 `{batch_id}-{slot_no:03d}`다 (US-2.5, W6)
  - 확인: 실행 뒤 SQLite 조회에서 `questions` 1행(`status`가 `passed` 또는 `dropped`+`drop_reason`)과 `verification_results` 1행이 있다. `passed`가 나올 때까지 반복한다.
- [x] T0.9 `quiz pool freeze`: `passed` 문제로 풀 스냅샷을 만든다. ID는 `"ps_" + sha256(...)[:12]`다 (US-3.1, W7)
  - 확인: 두 번 실행해도 같은 `pool_snapshot_id`가 나오고 `pool_snapshot_items`에 문제 ID가 있다.
- [x] T0.10 FastAPI 최소판: `GET /api/health`, `POST /api/sets`, `POST /api/sets/{set_id}/answers`. 단일 선택 채점(정답 키 일치)만 둔다. 서버 시작 시 마이그레이션을 적용한다. M0 임시: 풀이 10개 미만이면 있는 만큼 낸다 (US-4.1, US-4.3, W8, W9)
  - 확인: curl로 세트를 만들면 응답에 정답 키·해설·매핑·근거가 없고, 답을 보내면 `correct`, 정답 키, `explanation_ko`, `segments`, 근거 URL·quote가 온다. `attempts`에 1행이 생긴다.
- [x] T0.11 `web/` React + Vite(`react-ts`)와 `/api` 프록시. 세트 시작 버튼과 영어 문제·보기 화면 (US-0.1, US-4.2, W10)
  - 확인: `npm run dev` 뒤 `localhost:5173`에서 세트를 시작하면 영어 문제와 보기만 보이고, 개발자 도구 네트워크 응답에 정답 키가 없다.
- [x] T0.12 답 제출과 결과 화면: 정답 여부, 정답 키, 한국어 해설, 영·한 구절 매핑 표, 근거 링크(`https://docs.langchain.com` + `page`)와 인용 (US-4.2, W10)
  - 확인: 브라우저에서 문제 1개를 풀면 결과 화면에 다섯 항목이 모두 보이고 근거 링크가 실제 문서 페이지를 연다.
- [x] T0.13 M0 처음부터 끝까지 다시 돌리기: 빈 DB에서 migrate → generate → pool freeze → 서버·웹 → 풀이를 순서대로 적은 `docs/03-implementation/output/m0-smoke.md`를 만든다
  - 확인: `data/quiz.db`를 지우고 문서 순서대로 따라 하면 결과 화면까지 간다.

## M1 결정적 로직과 근거 자료 완성 (모델 없이 테스트)

- [x] T1.1 `gates.py` 나머지: 단답 허용 답안 1~5개, 단답 채점 정규화(대소문자, 공백, 백틱, 끝 `()`), 유사 중복(같은 quote, 토큰 Jaccard ≥ 0.6) (US-2.1, W3)
  - 확인: `uv run pytest tests/test_gates.py`가 새 규칙의 경계값(Jaccard 0.59/0.60, 답안 0/1/5/6개)을 포함해 통과한다.
- [x] T1.2 `grading.py`: 형식별 채점 함수 등록(단일, 복수, 단답, 코드 선택). 복수 선택은 부분 점수 없음. 형식을 DB `CHECK`로 고정하지 않는다 (US-4.3, W8)
  - 확인: `uv run pytest tests/test_grading.py`가 형식마다 정답·오답 사례를 통과하고, 등록 안 된 형식은 명확한 오류를 낸다.
- [x] T1.3 백업: 마이그레이션과 배치 전에 `sqlite3` backup API로 `data/backups/`에 백업한다. 보관 개수를 정해 설계서 1.4에 적는다 (US-0.2, W1)
  - 확인: `uv run quiz migrate` 뒤 `data/backups/`에 새 파일이 생기고 그 파일을 열면 같은 테이블이 있다.
- [x] T1.4 `quiz allowlist build`: `page-allowlist.md` 표를 읽어 `allowlist.yaml`(행마다 `snapshot`, `sha256`, `fetched_at`)을 만들고 해시가 다르면 멈춘다 (US-1.1, W2)
  - 확인: 스냅샷 파일 1바이트를 바꾸면 명령이 오류로 멈추고, 되돌리면 통과한다.
- [x] T1.5 스냅샷 수집 1/2: RAG, LangGraph 기초, Tool·MCP 버킷의 허용 목록 페이지 (US-1.1, W2)
  - 확인: 세 버킷의 `allowlist.yaml` 행마다 스냅샷 파일이 있고 크기가 MCP `wc -c` 값과 같다.
- [x] T1.6 스냅샷 수집 2/2: 미들웨어·HITL·가드레일, 멀티 에이전트, 운영 품질 버킷과 API 레퍼런스(`get_symbol` 출력) (US-1.1, W2)
  - 확인: `uv run quiz allowlist build`가 모든 행에서 해시 검사를 통과한다.
- [x] T1.7 슬롯 계획 함수: 버킷당 10개, 형식별 10개 이상, MCP 주제와 `없음` 주제에 코드 선택 배정 안 함, `근접` 주제 표시 (US-2.4, W6)
  - 확인: `uv run pytest tests/test_slots.py`가 60슬롯의 버킷·형식 개수와 금지 배정 0건을 확인한다.

## M2 파이프라인 완성

- [x] T2.1 `generate` 4형식: 복수 선택(`select_count`), 단답(`accepted_answers`), 코드 선택(`exec_spec`, `doc_url`), 버킷·유형·CCA-F 태그·조회 날짜, `근접` 주제 금지 문구 (US-2.2, US-2.4, W6)
  - 확인: 형식마다 슬롯 1개를 노드 단독 실행하면 스키마 검증을 통과한다.
- [x] T2.2 `judge` 완성: 정답, 근거 지지, 오답 보기, 매핑 충실도, 빠진 단답 변형(합쳐 최대 5개), 코드형 보기별 예측 `{ok, stdout, error_type}` (US-2.2, W6)
  - 확인: 일부러 정답 키를 틀린 문제를 넣으면 `judge_fail:<항목>`이 나온다.
- [x] T2.3 재생성 루프: feedback 노드, 실패 이유를 다음 생성 입력에 넣기, 최대 3회, `regen_exhausted`, 시도마다 `verification_results` 1행 (US-2.2, W6)
  - 확인: 항상 실패하는 가짜 게이트로 돌리면 시도 4행(0~3)과 `dropped`/`regen_exhausted`가 남는다.
- [x] T2.4 `sandbox/` uv 프로젝트: 고정 버전(GR-7.2), `fakes.py`(`GenericFakeChatModel`, `bind_tools` 하위 클래스), `runner.py`(stdin JSON → stdout JSON) (US-2.3, W5)
  - 확인: 예제 JSON을 `uv run python runner.py`에 넣으면 `{ok, stdout, error_type}` 한 줄이 나온다.
- [x] T2.5 `sandbox_client.py`와 `execute` 노드: `AWS_*`·`LANGFUSE_*` 제거, 보기당 30초, lock 해시, `judge_exec_mismatch`·`version_conflict` 판정 (US-2.3, W5)
  - 확인: `uv run pytest tests/test_sandbox_client.py`가 정상, 무한 루프(`timeout`), 환경 변수 미전달, 두 불일치 사례를 통과한다.
- [x] T2.6 `dedupe` 노드 연결과 노드 순서 확정(생성 → Judge → 실행 → 게이트 → 중복) (US-2.2, D-10)
  - 확인: 같은 quote 문제를 두 번 만들면 두 번째가 `duplicate`로 재생성 없이 버려진다.
- [x] T2.7 배치 CLI 완성: `--plan pilot|pool`, `--count N`, 슬롯 선기록, upsert, 동시 호출 2, `--resume <batch_id>` (US-2.5, W6)
  - 확인: 배치를 중간에 끊고 `--resume`하면 `passed`·`dropped`가 아닌 슬롯만 다시 돈다.
- [x] T2.8 토큰·비용: `verification_results`, `batches`에 토큰 누적, `data/pricing/bedrock.yaml`(AWS 가격 페이지 확인, 출처 URL, 날짜)로 `cost_usd` 계산 (US-2.5, US-7.2, W4)
  - 확인: 배치 1회 뒤 `batches.input_tokens`가 시도 행 합과 같고 단가가 있으면 `cost_usd`가 NULL이 아니다.
- [x] T2.9 Langfuse 선택 적용: SDK 키 이름 확인, 환경 변수 3개가 모두 있을 때만 콜백, `batch_id`를 세션 ID·태그로 (US-7.1, W4)
  - 확인: 환경 변수 없이 배치가 성공하고, 있으면 Langfuse UI에 그 `batch_id` trace가 1개 이상 있다.
- [x] T2.10 `quiz crosscheck --pool <pool_snapshot_id> | --batch <batch_id>`: Claude 계열이 아닌 모델 2개(`us.amazon.nova-pro-v1:0`, `openai.gpt-oss-120b-1:0`)가 정답 키를 보지 않고 `passed` 문제를 풀어 정답 키 오류 후보를 찾는다. 요구사항 밖 보조 점검(사용자 승인 2026-11-05). 모델에는 `stem_en`, 보기, 형식, `select_count`, 근거 페이지 스냅샷 원문만 준다. 정답 키, 허용 답안, 해설, 매핑, quote, `answer_basis`는 주지 않는다. 코드형은 기본으로 건너뛴다. 리전이 `us-east-1`이 아니면 오류로 멈춘다. `grading.py`로 채점해 `data/crosscheck/<대상 ID>.json`에 문항별 두 모델의 답·일치 여부·근거 문장을 쓰고 불일치 요약 표를 낸다. DB, migrations, `status`는 바꾸지 않는다. 첫 실행은 T3.1 직후다
  - 확인: 파일럿 배치에 돌리면 문항마다 모델 2개의 결과가 파일에 있다.
  - 판정: 두 모델 모두 정답 키와 다르면 감사 1순위, 한 모델만 다르면 2순위, 둘 다 `unanswerable`이면 근거 약함 신호다. 걸린 문항은 D-5 감사 표본과 별도로 사용자가 T5.1 전에 검토하고 파일의 `reviewed`(`ok`, `key_error`, `weak_grounding`, `ambiguous` 중 하나)에 적는다. `audit_records`에는 쓰지 않는다. 오류로 확인한 문항은 `audit_failed`로 바꾸고 다시 채운 뒤 freeze한다
- [x] T2.11 출제 품질 기준: 생성 프롬프트와 Judge에 좋은 문제 기준을 넣는다. 사용자 요청(2026-11-05). 스키마와 DB는 바꾸지 않는다. T3.1 파일럿 전에 끝낸다 (US-2.2)
  - 생성 프롬프트(`generate.md` 또는 `prompts/formats/<형식>.md`):
    1. 정의를 떠올리는 문제는 내지 않는다. 코드, 로그, 상황 같은 자료를 본문에 두고 적용·진단·판단을 묻는다.
    2. (선택형: `single`, `multi`, `code`) 오답 보기마다 그럴듯한 오해 하나를 담는다. 예: 증상만 해결, 맞는 패턴을 틀린 맥락에 적용. 말이 안 되는 보기는 금지한다.
    3. (선택형) 단서를 금지한다: 본문 단어를 정답에 되풀이, 오답에만 절대어(only/always/never), 정답만 유난히 긴 보기.
    4. `explanation_ko`에 보기마다 왜 맞고 왜 틀린지 한 문단씩 쓰고, 판단마다 근거를 문서 인용으로 든다. 단답은 대표 답과 허용 답안의 근거를 쓴다.
  - Judge(`judge.md`, `JUDGE_ITEMS`): 선택형에 `distractors_plausible`(2번), `no_cue`(3번)를 더한다. 실패하면 `judge_fail:distractors_plausible`, `judge_fail:no_cue`다. 기존 `distractors_wrong`은 그대로 둔다.
  - 확인: (1) `uv run pytest`에서 프롬프트에 네 규칙 문구가 있고, 단답 프롬프트에는 2·3번이 없다. (2) 가짜 Judge 응답으로 두 항목이 false면 두 실패 이유가 나온다. (3) 실제 Judge로 단서가 든 문제 1개(정답만 길고 오답에만 절대어)를 넣으면 `judge_fail:no_cue`가 나온다.
  - 완화: 생성 모델 일일 토큰 한도가 병목이다. T3.1 파일럿에서 두 항목 때문에 Judge 통과율이 크게 떨어지거나 `regen_exhausted`가 늘면, 두 항목을 실패 조건에서 빼고 `verification_results`에 경고로만 남긴다. 판단과 숫자를 기록 파일에 적는다.
  - 기준 예시: 사용자가 준 샘플. 나쁜 예는 정의 회상, 말이 안 되는 오답, 본문 반복·절대어 단서. 좋은 예는 연결 trace를 읽고 원인을 진단한 뒤 고치는 방법을 고르는 문제(오답 A는 증상만 해결, C는 맞는 패턴을 틀린 맥락에 적용, 보기별 해설). 원문은 대화에만 있어 저장소에 없다

## M3 파일럿과 축소 판단

- [x] T3.1 `quiz generate --plan pilot`(6문제)을 돌리고 문제당 시간, 토큰, 비용, Judge 통과율, 버린 이유, 요청 제한 발생 여부를 기록한다 (US-2.6, W7)
  - 확인: 기록 파일에 6문제 측정값과 60문제 소요 추정이 있다.
- [x] T3.2 축소 판단: 2026-11-06 09:00에 passed 수를 세고, 30개 미만이면 SERVICE.md 7.2의 2, 3번을 적용해 `data/waivers.yaml`에 더한다. 파일럿 직후에는 추정으로 미리 판단해 둔다
  - 확인: 판단 결과와 근거 숫자가 기록 파일에 있다.
  - 결과(2026-11-05 13:42): passed 60으로 기준 30을 넘어 축소하지 않는다. T4.1에서 60개를 채워 체크포인트 전에 최종 판단했다. 기록은 04-m3.md다.

## M4 풀 배치와 풀이 기능 완성 (배치가 도는 동안 서버·UI)

M4는 T4.1, T4.6, T4.7 확인으로 2026-11-05 13:39에 완료했다(사용자 확인). T4.8, T4.9는 뒤에 더한 작업이라 끝나는 조건에 넣지 않았고 따로 한다.

- [x] T4.1 `quiz generate --plan pool` 실행과 재개 (US-2.5, W7). 부족분은 `--plan fill`(design.md 7.2) 보충 9회로 채웠다
  - 확인: SQLite 조회로 `passed`가 버킷당 10개, 형식마다 10개 이상이다.
- [x] T4.2 `sets.py` 완성: 항상 10문제(M0 임시 규칙 제거), 복습 최대 3개 → 새 문제 → 맞힌 적 있는 문제 오래된 순, `retired` 제외 (US-4.1, W8)
  - 확인: `uv run pytest tests/test_sets.py`가 첫 세트, 복습 3개 초과, 새 문제 소진 사례를 통과한다.
- [x] T4.3 `review.py`: `n+2`, 1회차 오답 `m+5`, `cleared`, `retired`, 태그 갱신, 개념 실수 변형 대체 (US-5.2, US-5.3, W8)
  - 확인: `uv run pytest tests/test_review.py`가 간격 계산과 상태 전이를 모두 통과한다.
- [x] T4.4 API 완성: `PUT /api/attempts/{id}/tag`, `GET /api/sets/{set_id}`, 태그 없는 오답 409, 오답 행에만 태그 (US-4.4, US-5.1, W9)
  - 확인: `uv run pytest tests/test_api.py`(TestClient)가 409 두 사례와 이어 풀기 응답을 통과한다.
- [x] T4.5 UI 형식 컴포넌트: 복수 선택(고를 개수 표시), 단답 입력, 코드 선택(코드 블록, "코드 보기" 링크) (US-4.2, W10)
  - 확인: 형식마다 문제 1개를 브라우저에서 풀어 결과 화면까지 간다.
- [x] T4.6 UI 오답 태그와 이어 풀기: 독해/개념 선택, 독해면 구절 선택, 태그 전 다음 문제 막기, 새로고침 뒤 복원 (US-4.4, US-5.1, W10)
  - 확인: 오답에 태그 없이 다음으로 못 가고, 새로고침해도 푼 문제 결과가 그대로 보인다.
- [x] T4.7 UI 코드 표시: 문제 문장, 보기 문장, 해설에서 마크다운 코드 블록(```)은 `<pre><code>`로, 인라인 코드(`` ` ``)는 `<code>`로 보인다. 새 패키지 없이 작은 함수로 나누고 나머지는 문자열 그대로 출력한다. 사용자 요청(2026-11-05) (US-4.2, W10)
  - 확인: 문제 문장에 코드 블록이 든 문제 1개를 브라우저에서 열면 코드가 문장과 구분된 블록으로 보인다.
- [x] T4.8 UI 문제 메타 표시: 문제 문장 위에 주제(`bucket` 한글 라벨), 형식(단일 선택, 복수 선택 N개, 단답, 코드 선택), 복습 여부를 보인다. 서버는 세트 응답(`POST /api/sets`, `GET /api/sets/{set_id}`)의 문제마다 `review`를 더한다. 이전 `set_no`에서 원래 문제(`variant_of` 포함)를 푼 기록에 오답이 있으면 `"wrong"`, 정답만 있으면 `"seen"`, 없으면 `null`이다. `attempts`에서 계산하고 스키마는 바꾸지 않는다. `topic`은 정답 힌트가 될 수 있어 풀이 전에 보이지 않는다(FR-2.1). 응답 필드 추가는 기록 파일 "결정" 표에 적는다. T5.3 커밋 뒤에 한다. 사용자 요청(2026-11-05) (US-4.2, W10)
  - 확인: `uv run pytest`가 `review` 세 경우를 통과하고, 브라우저에서 새 세트의 모든 문제 위에 주제·형식 표시가 보이며 이전 세트에서 푼 문제에 복습 표시가 보인다.
- [x] T4.9 UI 소프트 카드 테마: 연회색 배경(`#f4f5f9`) 위 흰 문제 카드(둥근 모서리, 옅은 그림자), 남색 포인트(`#4263eb`), 메타는 알약 배지, 보기는 둥근 상자와 원형 번호 배지, 판정은 색 띠. 처음 정한 에디토리얼 테마는 사용자가 화면을 보고 바꿨다(2026-11-05). 글꼴은 Pretendard(`index.html`에 CDN 링크 1줄, 실패하면 지금 글꼴로 대체). 색·글꼴·간격은 `:root` 변수로 모아 감사 화면(T5.3)에도 같이 적용한다. 새 npm 패키지는 넣지 않는다. 기능과 마크업 구조는 바꾸지 않는다. T4.8 뒤에 한다. 사용자 요청(2026-11-05) (US-4.2, W10)
  - 확인: 브라우저에서 형식 4개의 문제와 결과 화면, 오답 태그, 감사 화면을 열어 테마가 적용되고 깨진 배치가 없다. `uv run pytest`와 `npm run build`가 통과한다.

## M5 풀 고정과 감사

- [x] T5.1 `pool freeze` 최종: 변형 제외, 60개 확인. 그 전에 T2.10 걸린 문항 검토를 끝낸다 (US-3.1, W7)
  - 확인: `pool_snapshot_items`가 60행이고 변형 문제가 없다.
  - 결과(2026-11-05 13:53): `ps_326384fb5422` 60행, 변형 0, 버킷마다 10. 교차 풀이 걸린 문항 4개 검토 뒤 2개를 `audit_failed`로 빼고 rag 2개를 다시 채웠다. 기록은 06-m5.md다.
- [x] T5.2 `audit.py`와 감사 API: 시드·표본(D-5), 같은 스냅샷이면 기존 감사, 문항별 기록, 20개 차면 `result` 계산 (US-3.2, W11)
  - 확인: `uv run pytest tests/test_audit.py`가 같은 스냅샷 같은 표본, 기준 경계값(오류 1/2개)을 통과한다.
- [x] T5.3 감사 화면: 문항마다 정답 키, 근거, 매핑과 세 판정 입력 (US-3.2, W10)
  - 확인: 브라우저에서 1문항을 기록하면 `audit_records`에 1행이 생긴다.
- [x] T5.4 본인 감사 20문항 1/2 (10문항)
  - 확인: `audit_records`가 10행이다.
- [x] T5.5 본인 감사 20문항 2/2 (10문항)
  - 확인: `audits.result`가 `pass` 또는 `fail`이다.
  - 결과(2026-11-05 14:19): `au_326384fb5422` `pass`. 정답 키 오류 0, 인용 미지지 0, 매핑 불충실 1. T5.6은 필요 없다.
- [ ] T5.6 감사 미달 처리(필요할 때만): `audit_failed`, 재채움, 새 스냅샷 재감사, 마감까지 미달이면 `data/waivers.yaml` (US-3.3, W11)
  - 확인: 새 `pool_snapshot_id`의 감사 `result`가 `pass`이거나 `waivers.yaml`에 미달 목록이 있다.

## M6 완료 조건 확인

- [x] T6.1 `quiz metrics`: `data/metrics/baseline.json`(Judge 통과율, 버린 이유별 개수, 세트별 정답률, 배치별 토큰·비용·초) (US-7.2, W13)
  - 확인: 파일이 설계서 5.4 형식의 키를 모두 가지고 숫자가 SQLite 조회와 같다.
- [x] T6.2 3세트 풀이와 모든 오답 태그 (W14)
  - 확인: 서버를 다시 시작한 뒤 SQLite 조회에서 서로 다른 `set_id` 3개 × 10행, 태그 없는 오답 0행, `reading` 행은 모두 `confused_segment_id`가 있다.
- [x] T6.3 MVP 완료 조건 4개(SERVICE.md 4.1) 점검표를 `docs/03-implementation/output/`에 쓴다
  - 확인: 네 조건마다 측정 쿼리와 결과 값이 있다.

## M7 축소 대상

- ~~T7.1 `quiz generate --variants`~~ (US-6.1, W12). 2026-11-05 면제(SERVICE.md 7.2 1번). 복습 큐는 원래 문제로 충족한다(T4.3)
  - 확인: `data/waivers.yaml`에 변형 문제 면제 항목이 있다.
- [x] T7.2 2026-11-06 17:00 전에 Langfuse UI trace 1회 내보내기 (US-7.3). 체크포인트에서 빠질 수 있다
  - 확인: 내보낸 파일이 저장소에 있다.
