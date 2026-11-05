# M0 최소 경로 실행 순서

상태: 초안
작성일: 2026-11-05
작업: [TASKS.md](../../../TASKS.md) T0.13

빈 DB에서 생성부터 풀이 결과 화면까지 한 경로를 돌리는 순서다. M0 범위는 단일 선택 1개 슬롯 종류, 주제 1개(`/oss/python/langgraph/graph-api`), 생성 → Judge → 게이트 1회다.

## 사전 조건

| 항목 | 값 |
| --- | --- |
| AWS 자격 증명 | 저장소 루트 `.env`의 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`. `quiz generate`만 읽는다 |
| 리전 | `AWS_REGION`, 없으면 `AWS_DEFAULT_REGION`. `us-east-1`, `us-west-2`, `ap-northeast-2` 중 하나 |
| 도구 | uv, Node·npm |
| Git Bash | 문서 경로 인자를 넘길 때 `MSYS_NO_PATHCONV=1`을 붙인다. 없으면 `/oss/...`가 Windows 경로로 바뀐다 |

## 순서

`app/`에서 1~4를 실행한다.

| # | 명령 | 확인 |
| --- | --- | --- |
| 0 | `rm ../data/quiz.db` | 빈 DB에서 시작한다 |
| 1 | `uv run quiz migrate` | `applied=[1] schema_version=1` |
| 2 | (스냅샷이 없을 때만) `MSYS_NO_PATHCONV=1 uv run quiz snapshot fetch /oss/python/langgraph/graph-api` | `sha256=cd6c0535...`가 `packs/langchain/allowlist.yaml` 값과 같다 |
| 3 | `uv run quiz generate --plan pool --count 1` | `<question_id> passed`. `dropped`이면 다시 돌린다. pool 계획의 슬롯 1(rag 단답)만 돈다 |
| 4 | `uv run quiz pool freeze` | `pool_snapshot_id=ps_...` |
| 5 | `uv run uvicorn quiz.server:app --port 8000` | `Application startup complete` |
| 6 | `web/`에서 `npm install`(처음 한 번), `npm run dev` | `http://localhost:5173` |
| 7 | 브라우저에서 "새 세트 시작" → 보기 선택 → "제출" | 결과 화면에 정답 여부, 정답 키, 해설, 영·한 구절 매핑, 근거 링크와 인용이 보인다 |

## 검증 결과 (2026-11-05)

| 작업 | 결과 |
| --- | --- |
| T0.1 | `langchain` 1.4.7, `langgraph` 1.2.17, `fastapi` 0.162.0, `langchain-aws` 1.9.0 import 성공. `app/uv.lock`, `app/.python-version`(3.14.8)이 `git status`에 보인다 |
| T0.2 | `quiz migrate` 두 번 실행. 두 번째는 `applied=[]`. 테이블 13개 |
| T0.3 | 스냅샷 31,352B. sha256 `cd6c0535bd600706a39b31698beb0545b8b9643c03827eeaedda328343e0668e`가 MCP 서버 `sha256sum`, 로컬 `sha256sum`, `allowlist.yaml`과 같다 |
| T0.4 | `tests/test_gates.py` 7개 통과 |
| T0.5 | 생성·Judge 모델이 `pong` 응답(토큰 13/5). `AWS_REGION=eu-west-1`은 `RegionError`(`tests/test_llm.py`) |
| T0.6 | 생성 노드 1회: 스키마 검증 통과, 게이트 통과. 10.6초, 입력 10,115·출력 825 토큰 |
| T0.7 | 그래프 1회: Judge 네 항목 모두 true, 게이트 통과, `passed`. 17.0초 |
| T0.8 | `questions` 1행 `passed`, `verification_results` 1행(인용·매핑·Judge 1), `batches` 토큰 20,771/1,178 |
| T0.9 | `pool freeze` 두 번 모두 `ps_4a569e6604dc`. `pool_snapshot_items` 1행 |
| T0.10 | `tests/test_api.py` 2개 통과. curl: 세트 응답에 정답 키·해설·매핑·근거 없음. 답 제출 응답에 `correct`, `answer_key`, `explanation_ko`, `segments`, 근거 URL·quote. `attempts` 1행 |
| T0.11 | `npm run build` 통과. Vite 프록시로 `/api/health`, `POST /api/sets` 응답. 세트 응답 필드는 `bucket, choices, format, question_id, select_count, stem_en`뿐이다. 브라우저 화면은 사용자가 확인했다(2026-11-05) |
| T0.12 | 프록시로 답 제출 응답 확인(매핑 3개, 근거 URL `https://docs.langchain.com/oss/python/langgraph/graph-api`, HTTP 200). 결과 화면 다섯 항목은 사용자가 브라우저에서 확인했다(2026-11-05) |
| T0.13 | 빈 DB에서 1, 3, 4, 5를 다시 돌려 2문제 `passed`, `ps_72e06774fd2b`. 34.7초. 프록시로 세트·답 제출까지 확인. 7번 브라우저 단계는 사용자가 확인했다(2026-11-05) |

전체 테스트: `uv run pytest` 12개 통과.
