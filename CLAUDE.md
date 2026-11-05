# ax_transformation_miniPJT

LLM 학습 문제 풀이 웹앱 과제(agent-dev-quiz). LangChain 팩을 먼저 만들고, CCA-F 팩은 다음에 붙인다.
현재 단계와 일정, 마감은 `TASKS.md`를 따른다.

## 기준 문서
문서끼리 다르면 요구사항 정의서가 우선한다. 구현 값은 설계서를 따른다.

| 문서 | 용도 |
| --- | --- |
| `docs/01-requirements/output/requirements.md` | 요구사항 |
| `docs/02-spec-design/output/design.md` | 구현 값(스키마, 노드 순서, 실패 이유, 디렉토리 4.1) |
| `docs/02-spec-design/output/seed.yaml` | 수용 기준 |
| `SERVICE.md` | PRD. 새 요구사항을 더하지 않는다 |
| `TASKS.md` | 구현 작업 순서와 일정. 작업은 `확인:` 줄이 통과해야 끝난다 |
| `docs/03-implementation/output/implementation.md` | 구현 결과(코드 구조, 검증 결과) |
| `docs/dev-process/NN-<stage>-plan.md` | 현재 단계 계획. 병렬 실행 표가 있다 |

## 디렉토리
- `docs/NN-<stage>/input/`, `output/`: 단계별 입력과 산출물이다. 앞 단계 output은 복사하지 않고 링크한다. 단계는 `docs/dev-process/skillset-by-lifecycle.md`를 따른다.
- `docs/dev-process/`: 단계 계획(`NN-<stage>-plan.md`)과 수행 기록(`NN-<stage>/0K-<묶음>.md`)을 둔다.
- 코드는 `docs/` 밖에 둔다. 구조는 `design.md` 4.1을 따른다.
  - `app/`: Python 앱(uv 프로젝트, 패키지 `quiz`)
  - `web/`: React + Vite
  - `sandbox/`: 코드 선택 문제 실행 환경(M2)
  - `packs/langchain/`: 스냅샷, `allowlist.yaml`, 프롬프트
  - `data/`: `quiz.db`, 백업, `waivers.yaml`, 지표

## 명령
| 위치 | 명령 | 용도 |
| --- | --- | --- |
| `app/` | `uv run pytest` | 전체 테스트 |
| `app/` | `uv run quiz migrate` | 스키마 적용 |
| `app/` | `MSYS_NO_PATHCONV=1 uv run quiz snapshot fetch <page...>` | 문서 스냅샷 수집 |
| `app/` | `uv run quiz generate --plan pilot\|pool\|fill [--count N]`, `--resume <batch_id>` | 문제 생성(Bedrock 호출) |
| `app/` | `uv run quiz crosscheck --batch <batch_id>` 또는 `--pool <id>` | 교차 풀이 점검(T2.10, Bedrock 호출, us-east-1만) |
| `app/` | `uv run quiz pool freeze` | 풀 스냅샷 |
| `app/` | `uv run quiz metrics` | `data/metrics/baseline.json`을 다시 쓴다 |
| `app/` | `uv run quiz allowlist build` | `allowlist.yaml`을 만들고 스냅샷 해시를 검사한다 |
| `app/` | `uv run uvicorn quiz.server:app --port 8000` | API 서버 |
| `web/` | `npm run dev` | `http://localhost:5173`, `/api`를 8000으로 넘긴다 |

처음부터 끝까지 도는 순서는 `docs/03-implementation/output/m0-smoke.md`에 있다.
`quiz` 명령은 기본으로 `data/quiz.db`를 쓴다. 다른 DB를 쓰려면 `QUIZ_DB`에 경로를 준다.

## 고정 결정
- 모델 호출은 AWS Bedrock 경유로 한다. Anthropic API는 직접 부르지 않는다. 쓸 수 있는 모델은 `docs/01-requirements/input/bedrock-model-list.md`를 따른다(Claude, Amazon Nova).
- 리전은 `us-east-1`, `us-west-2`, `ap-northeast-2` 중 하나다. `AWS_REGION`을 읽고, 없으면 `AWS_DEFAULT_REGION`을 읽는다.
- 정답과 해설의 근거는 공식 문서 원문 인용만 인정한다. 학습 노트는 탐색용이다.
- 문제는 영어, 해설은 한국어로 쓴다. 형식은 단일 선택, 복수 선택, 단답, 코드 선택이다.

## 작업 규칙
- 테스트를 먼저 쓰고, 실패를 본 뒤 구현한다.
- 구현하다가 `design.md`와 다른 값을 정하면 기록 파일의 "결정" 표에 적는다. `design.md`는 차이를 사용자에게 보이고 승인받은 뒤 고친다.
- 확인하지 못한 사실은 "미확인"으로 쓴다. 날짜는 절대 날짜(YYYY-MM-DD)로 쓴다.

## 비밀과 환경
- 자격 증명은 저장소 루트 `.env`에 있다. 값은 기록 파일, 로그, 커밋 어디에도 쓰지 않는다.
- `.env`는 `quiz generate`, `quiz crosscheck` CLI만 읽는다. 서버와 샌드박스에는 `AWS_*`, `LANGFUSE_*`를 넘기지 않는다.
- Git Bash는 `/oss/...` 인자를 Windows 경로로 바꾼다. 문서 경로를 넘길 때는 `MSYS_NO_PATHCONV=1`을 붙인다.
- `packs/langchain/snapshots/`는 줄바꿈 변환을 하지 않는다(`.gitattributes`). 손으로 고치지 않는다. 바이트가 바뀌면 sha256 검사에서 실패한다.
- 백틱이 든 파일은 셸 heredoc으로 쓰지 않는다. 파일 쓰기 도구로 쓴다.

## 세션과 병렬 작업
- 진행 상태의 기준은 파일이다(`TASKS.md` 체크박스, 기록 파일의 "인계" 절). 세션 하나는 묶음 하나까지 하고, `/stage <NN> run`으로 이어 간다.
- 코디네이터(사용자와 대화하는 세션)만 쓰는 파일: `TASKS.md`, `docs/` 전체, `app/pyproject.toml`, `app/uv.lock`, `app/migrations/`, `web/package.json`, `web/package-lock.json`. Bedrock 호출과 `.env`가 필요한 작업은 코디네이터 worktree에서만 돌린다.
- 새 단계 worktree에는 git에서 빠진 `.env`와 `data/quiz.db`가 없다. 코디네이터 worktree를 만들면 둘을 복사해 온다.
- 병렬 워커 절차는 stage 스킬 run 3번과 단계 계획의 "병렬 실행" 표를 따른다.
