# 03 interrogate 기록

상태: 진행 중
시작: 2026-11-06 09:22(공격자 C 소요 653초와 09:35 이전 완료로 거꾸로 셈. 분 단위는 미확인)
완료:
계획: [05-evaluation-review-plan.md](../05-evaluation-review-plan.md)의 3단계
세션 모델: Opus 5.5(`claude-opus-5-5`). 공격자 서브에이전트는 같은 모델을 이어받는다(미확인. 서브에이전트 정의의 기본값). 추론 강도: 미확인

## 입력

- 기준 커밋: `3a48c4cb463e2023ce5d5cd7a36f011cc44bb965`. 평가 대상 커밋 `01898460` 뒤에 기록만 더했다. 코드는 같다
- 공격자 3명: worktree 격리 서브에이전트(general-purpose), 한 메시지에서 동시에 띄웠다(약 09:22)

### 의도 재진술

- 학습자는 고정 풀에서 세트를 받는다. 제출 전에는 정답 키, 허용 답안, 해설, 매핑, 근거 인용이 어디에서도 보이지 않는다.
- 단일 선택, 복수 선택, 단답, 코드 선택 채점은 seed 수용 기준과 요구사항을 따른다. 오답은 정한 규칙대로 복습 큐에 들어가고 나온다.
- 통과 문제는 허용 목록 스냅샷(sha256 고정)의 원문 인용으로 근거가 있다. 결정적 검사에 실패한 문제는 이유와 함께 버린다. 유사 중복은 막는다. 배치 재개는 일을 되풀이하지 않는다. 실험 명령은 `data/quiz.db`를 쓰지 않는다. 고정 풀은 바뀌지 않는다.
- 모델 호출은 Bedrock만 쓴다. `.env`는 CLI 3개만 읽는다. 서버와 샌드박스는 `AWS_*`, `LANGFUSE_*`를 받지 않는다. 샌드박스는 네트워크, 시간, 호스트 비밀과 DB에서 격리된다.

### 공격자 지시

공통: 첫 줄 `git reset --hard 3a48c4c…`와 해시 확인. 지시문 "Break this product. Prove every claim by running it against the real code in your worktree." 범위는 제품 전체. Bedrock 호출 금지, `.env`와 `data/quiz.db` 없음, 임시 `QUIZ_DB`, 코드 수정과 커밋 금지, 약 60분. 발견마다 제목, 명령, 출력, 의도가 요구하는 출력, 깨는 의도. 버틴 시도도 한 줄씩. 끝에 브랜치, 해시, 커밋 없음 확인.

| 공격자 | 중심 영역 | 의도로 준 문서 |
| --- | --- | --- |
| A | 격리와 비밀(샌드박스 탈출, 네트워크, 제한, 서버·샌드박스 환경, 비밀을 읽는 곳) | 고정 결정(CLAUDE.md) 요약을 지시에 적었다 |
| B | API와 채점(제출 전 정답 노출, 형식별 채점 경계, 상태 전이, 입력 검사, 동시성) | `seed.yaml`, `requirements.md` |
| C | 생성 게이트와 데이터(인용 검사 우회, 허용 목록 밖 페이지, 유사 중복 경계, 재개 멱등, 실험·교차 풀이가 쓰는 DB, 스냅샷 변조 검출) | `seed.yaml`, `design.md` |

## 진행

### 공격자 보고(원문 요약)

공격자 A(소요 441초, 도구 호출 37회, 브랜치 `worktree-agent-a54b89f589e8a39ee` @ `3a48c4c`, 커밋 없음, 임시 파일 삭제). Docker 없음. 샌드박스는 `sandbox/.venv` Python으로 `runner.py`를 subprocess로 띄운다. 격리 수단은 같은 프로세스 안 socket 몽키패치, 환경 변수 접두사 제거, `subprocess.run(timeout=)` 셋이다.

| 번호 | 제목 | 핵심 출력 |
| --- | --- | --- |
| A-1 | 샌드박스 코드가 저장소 루트 `.env`와 저장소 밖 파일을 읽는다 | `open('../.env').read()`가 가짜 `AWS_SECRET_ACCESS_KEY=dummy-secret-123`을 돌려줌. `C:/Windows/win.ini`도 읽힘 |
| A-2 | `_socket` 직접 사용으로 네트워크 차단 우회, `.env` 반출 | `_socket` TCP `1.1.1.1:80` 연결 `CONNECTED`, DNS 조회, UDP 전송 성공. localhost 리스너가 가짜 `.env` 전문을 받음. `urllib`만 막힘 |
| A-3 | 샌드박스가 앱 DB를 읽고 쓴다. `QUIZ_DB`가 자식 환경에 넘어간다 | `sqlite3.connect(os.environ['QUIZ_DB'])`로 `pwned` 테이블 생성, 호스트에서 `[('from-sandbox',)]`. `../PWNED.txt` 쓰기 성공 |
| A-4 | 샌드박스 stdout의 비밀이 `verification_results.exec_result_json`에 저장된다 | `nodes.execute` → `store.upsert_verification` 경로에서 `DB row contains secret: True` |
| A-5 | 손자 프로세스가 시간 제한을 무력화한다 | 파이프를 물려받은 손자: `timeout=5`에 26.2초 막힘. 분리된 손자: 5.0초에 끝났지만 kill 뒤 파일을 씀 |
| A-6 | 샌드박스 코드가 결과 줄을 위조한다 | fd 3~19에 위조 JSON을 쓰고 `os._exit(0)` → `forged: {'ok': True, 'stdout': 'expected answer\n', ...}` |
| A-7 | 자식 환경 정리가 denylist다 | `GITHUB_TOKEN`, `BEDROCK_API_KEY`(가짜)와 `QUIZ_DB`, `USERPROFILE`이 샌드박스에 넘어감 |

A가 버틴 것: 샌드박스 `os.environ`에 `AWS_*`, `LANGFUSE_*` 없음. 손자 `cmd /c set AWS` 빈 출력. `urllib` 차단. fd 1 위조 실패. 단순 무한 루프는 timeout. 서버는 `.env`가 있어도 `os.environ`에 AWS/LANGFUSE 없음, `dotenv`·`quiz.env`·`quiz.llm`·`boto3`·`langfuse`를 로드하지 않음. 문서에 `.env`를 셸로 퍼뜨리는 안내 없음. 참고: 서버는 자기 환경을 지우지 않는다(셸에 export하면 받음, 실행하지 않음).
A가 실행하지 못한 것: 샌드박스에서 ctypes `ReadProcessMemory`로 부모 CLI 환경 변수 읽기. 자동 모드 권한 분류기가 거부했다. 코디네이터도 시도하지 않는다(권한 결정을 우회하지 않는다). 미확인으로 남긴다.

공격자 B(소요 432초, 도구 호출 34회, 브랜치 `worktree-agent-a601d18a699ed3e10` @ `3a48c4c`, 커밋 없음, 추적 안 되는 `app/probe_b*.py` 4개).

| 번호 | 제목 | 핵심 출력 |
| --- | --- | --- |
| B-1 | 오답 제출과 새 세트 생성이 겹치면 태그 없는 오답이 닫힌 세트에 남는다 | 동시 요청 후 태그 시도 `409 set_closed`, `wrong rows with NULL mistake_tag: [(151, 's043-…', 43)]`, 큐 항목 없음, 다음 세트 200 |
| B-2 | 같은 문제 동시 두 번 제출 시 409 대신 500 | `{409: 43, 200: 150, 500: 107}`, `sqlite3.IntegrityError: UNIQUE constraint failed: attempts.set_id, attempts.question_id` |
| B-3 | `POST /api/sets` 동시 요청 시 500 | 4병렬×20회 `{500: 55, 200: 25}`, `UNIQUE constraint failed: quiz_sets.set_no` |
| B-4 | 감사 실패 문제가 현재 풀에 남아 출제된다(영역 밖) | `freeze`가 `INSERT OR IGNORE`라 기존 스냅샷 `created_at`이 안 바뀜, `current_pool`이 `audit_failed` 문제가 든 풀을 고름, 세트 2개에 출제 |
| B-5 | 보기에 없는 답, 빈 답, 20만 자 답이 오답으로 저장되고 해설이 공개된다 | `'Z' 200`, `[] 200`, 길이 200004 저장 |
| B-관찰 | `POST /api/audits`, `GET /api/audits/current`가 표본 20문항의 정답 키와 해설을 조건 없이 준다 | design.md 7.1이 정한 동작. FR-2.1과의 긴장으로만 보고 |

B가 버틴 것: 세트 응답 문제 필드는 `bucket, choices, format, question_id, review, select_count, stem_en`뿐이고 답 전 `results`는 `{}`. 단일·복수·단답 채점 경계(4.4 규칙과 같음). 복습 큐 전이(세트 1 오답 due 3, 세트 3 오답 round 2 due 8, 세트 8 오답 retired, 이후 미출제). `untagged_wrong`, `set_closed`, `correct_row` 409. 잘못된 태그·segment 422. 경합에서도 UNIQUE가 중복 행을 막음.

공격자 C(소요 653초, 도구 호출 54회, 브랜치 `worktree-agent-a34f9d3aec1cb3e94` @ `3a48c4c`, 커밋 없음, `git status` 0줄). 스크립트와 임시 DB, 변조용 저장소 복사본은 코디네이터 스크래치 `c/` 아래에 있다. C의 전체 테스트는 368 passed, 6 failed(`test_sandbox_client`, 샌드박스 가상 환경 미설치. 발견에서 뺐다).

| 번호 | 제목 | 핵심 출력 |
| --- | --- | --- |
| C-1 | 워커 2개면 같은 버킷의 같은 문제가 둘 다 passed가 된다 | `process_slot`이 시작할 때 한 번만 같은 버킷 passed(`peers`)를 읽는다. `race.py 2`: `-001 passed`, `-002 passed`, `passed same-bucket identical stems: [('rag', 2)]`. 대조 `race.py 1`: `-002`~`-004 dropped duplicate` |
| C-2 | `--resume`이 `audit_failed` 문제를 다시 생성해 고정 풀 안 문제를 덮어쓴다 | `batch.DONE = ("passed", "dropped")`. 재개 전 `audit_failed 'Question alpha delta version 0'` → 뒤 `passed 'Question charlie romeo version 2'`, `still in frozen pool: 1`, 다시 고정해도 같은 `ps_b077d0ea109c` |
| C-3 | 교차 풀이가 스냅샷 sha256을 검사하지 않는다 | 변조 복사본에서 `run_batch`는 `AllowlistError`, `crosscheck finished without hash error`, `tampered text reached crosscheck prompt: True` |
| C-4 | 결정적 게이트가 내용 없는 인용(표 구분선)과 공백뿐인 `ko`를 통과시킨다 | `('b20261106-01-001', 'passed', '/oss/python/integrations/document_loaders', ' \| \| ------...------ \| \| ', '[{... "ko": "   "}]')`(가짜 Judge PASS) |
| C-5 | `\\?\` 접두 경로가 실험 DB 가드를 통과해 운영 DB에 쓴다 | `ALLOWED  \\?\ prefix`, `operational DB batches after = 1`(복사본 저장소) |

C가 버틴 것: 인용 30자 경계, 대소문자·한 글자·U+200B 변경은 `quote_mismatch`, NFKC·줄바꿈 차이는 통과, 근거 2개 중 1개만 꾸며도 실패, page 끝 `/`·전체 URL은 `page_not_allowed`, Jaccard 0.6 경계, 공백·백틱·대소문자만 다른 본문 duplicate, 워커 1개 재개, `quiz experiment judge`가 DB 바이트를 바꾸지 않음, 가드가 junction·8.3·끝 점·대문자·상대 경로·ADS를 막음, `run_batch`·`run_judge`는 변조 시 멈춤, `snapshot: null` 행 0. 경계 관찰: quote 앞 1글자만 빼도 "같은 quote" 검사를 피한다(사양과는 맞음).

### 코디네이터 검증(2026-11-06 09:30~09:35, 이 worktree)

A 검증: 스크래치 `ev/v_a.py`(실제 경로 `quiz.sandbox_client.run`). 실제 `.env` 대신 저장소 루트 가짜 파일 `zz-dummy-secret.txt`(`DUMMY_SECRET=fake-123`, 끝나고 지움)를 읽게 했다. 반출은 localhost 리스너로만 했다. 임시 DB `ev/tmp-va.db`.

| 번호 | 결과 | 출력 |
| --- | --- | --- |
| A-1 | 재현 | `open('../zz-dummy-secret.txt')` → `"DUMMY_SECRET=fake-123\n"`. `C:/Windows/win.ini` → `"; for 16-bit app support\n[font"` |
| A-2 | 재현 | `_socket`으로 localhost 연결·전송 `sent`, 리스너가 `b'DUMMY_SECRET=fake-123\r\n'`을 받음. 같은 연결을 `socket.socket`으로 하면 `NetworkBlockedError`. 바깥 인터넷 연결은 코디네이터가 다시 시도하지 않았다(A의 `1.1.1.1:80` 결과만 있음) |
| A-3 | 재현 | 샌드박스 `os.environ['QUIZ_DB']`가 임시 DB 경로. 샌드박스가 `pwned` 테이블을 만들고 호스트가 `[('sb',)]`을 읽음 |
| A-4 | 코드 경로 확인 | `nodes.execute`가 실행 결과(stdout 포함)를 `exec_result`에 넣고(260행) `store.upsert_verification`이 `exec_result_json`에 쓴다(`store.py` 99행). A-1과 합치면 비밀이 DB에 남는다 |
| A-5 | 재현 | 손자가 파이프를 물려받고 15초 잠: `timeout=5`인데 `elapsed_s: 16.0`, 결과 `timeout` |
| A-6 | 재현 | fd 3~19에 위조 JSON, `os._exit(0)`, 뒤에 `raise ValueError` → `{"ok": true, "stdout": "expected answer\n"}` |
| A-7 | 재현 | 가짜 `GITHUB_TOKEN`, `QUIZ_DB`, `USERPROFILE`이 넘어감. 가짜 `AWS_SECRET_ACCESS_KEY`는 지워짐 |

B 검증: B의 `probe_b.py`, `probe_b2.py`, `probe_b4.py`를 읽고(임시 DB만 씀) `app/`에 복사해 돌린 뒤 지웠다. 동시성은 임시 DB로 uvicorn `--port 18741`을 띄웠다.

| 번호 | 결과 | 출력 |
| --- | --- | --- |
| B-1 | 재현 | 첫 시도 `answer 200 wrong + new set 200 -> tag old attempt: 409 set_closed`, `wrong rows with NULL mistake_tag: [(1, 's001-331d7a89', 1)]` |
| B-2 | 재현 | `{409: 60, 200: 150, 500: 90}`, 서버 로그 `UNIQUE constraint failed: attempts.set_id, attempts.question_id` 90회 |
| B-3 | 재현 | `{500: 54, 200: 26}`, `UNIQUE constraint failed: quiz_sets.set_no` 54회 |
| B-4 | 재현 | `freeze after audit_failed -> ps_e9183e97416f count 20 == A? True`, `current_pool -> ps_5e25d74d9a05`, `audit_failed question served in sets: 2` |
| B-5 | 재현 | `'Z' 200 (False, ['Z'])`, `[] 200 (False, [])`, 긴 답 200 |
| B-관찰 | 다시 돌리지 않음 | design.md 7.1이 정한 동작이다. 5단계에 "관찰"로 올린다 |

C 검증: C의 스크립트(스크래치 `c/`)를 읽고 다시 돌렸다. 가짜 모델만 쓴다. 셸에 `LANGFUSE_*`, `AWS_*`가 없음을 확인했다(`env | grep -c` 0). C-1, C-2, C-4는 이 worktree 코드와 새 임시 DB(`c/v_*.db`)로, C-3, C-5는 C의 저장소 복사본(`c/repo`, 스크립트가 `REPO_ROOT`에 `scratchpad`가 있는지 assert)으로 돌렸다.

| 번호 | 결과 | 출력 |
| --- | --- | --- |
| C-1 | 재현 | 워커 2: `-001 passed`, `-002 passed`, `[('rag', 2)]`. 워커 1: `-001`만 passed, `[]` |
| C-2 | 재현 | `before resume: ('audit_failed', 'Question alpha delta version 0', …)`, `unfinished() = 1`, `after resume: ('passed', 'Question charlie romeo version 2', …)`, `still in frozen pool: 1`, `pool freeze now: ('ps_b077d0ea109c', 2)` |
| C-3 | 재현 | `run_batch after tamper: AllowlistError`, `crosscheck finished without hash error`, `tampered text reached crosscheck prompt: True` |
| C-4 | 재현 | `('b20261106-01-001', 'passed', '/oss/python/integrations/document_loaders', ' \| \| -----…', '[{… "ko": "   "}]')` |
| C-5 | 재현 | 경로 별칭 중 `\\?\` 접두만 `ALLOWED`. `operational DB batches before = 1` → `after = 2` |

C-3 재실행 뒤 복사본 스냅샷이 변조된 채 남았다(스크립트에 되돌리기 단계가 없다). 이 worktree 원본으로 복사본 파일만 되돌렸다(sha256 앞 16자 `cd6c0535bd600706` 일치). 이 worktree `packs/`는 바뀌지 않았다(`git status --short packs` 0줄).

### P5 결정적 도구(2026-11-06 09:34)

| 도구 | 명령 | 결과 |
| --- | --- | --- |
| bandit | `uv run --no-project --with bandit bandit -r app/quiz sandbox/runner.py -q` | High 0, Medium 3, Low 4. 모두 버렸다: `runner.py:96` exec는 샌드박스 설계 자체. `server.py:260` SQL은 `?` 자리표시자만 이어 붙임. `migrate.py:50`은 파일 이름에서 온 정수 버전. `audit.py:65`, `sets.py:50` random은 감사 표본·세트 뽑기(보안 용도 아님). `sandbox_client.py` subprocess는 인자 목록 호출 |
| hypothesis | 스크래치 `ev/fuzz_short.py`, `uv run --with hypothesis`(pyproject 그대로) | 성질 4개(대소문자·공백·백틱·끝 `()` 변형은 정답, 한 글자 바꾸면 오답, 임의 문자열에 예외 없음, 공백·백틱·괄호뿐인 허용 답안에 빈 제출은 오답) 각 2,000~3,000건. 실패 0 |
| 샌드박스 소켓 | A-2 검증 | 재현(위 표) |

P5 결정적 도구 중 "샌드박스 안 실제 소켓 시도"는 A-2 검증이 대신한다. A는 예시 없이 `_socket` 우회를 찾았다(P4 기준 "독립 발견"). 03 8장 기술 부채와 같은 내용이다.

운영 DB 관찰(2단계 증거 수집 중): `data/quiz.db` `attempts` 41번(`s010-c3c367fa`, 2026-11-05T08:44:56Z, 답 `["몰라"]`, 오답, 태그 없음)은 03 측정(05:47Z) 뒤에 생긴 미완료 세트의 마지막 답이다. 태그를 고르기 전에 멈춘 상태로 보인다. B-1 경합 흔적은 아니다(세트 `s010`에 답이 1개뿐이고 뒤에 세트가 없다).

## 인계

갱신: 2026-11-06 09:35
- 마지막 완료 작업: 공격자 3명 보고 검증(17건 재현, 버림 0), P5 도구 실행
- 다음 작업: 5단계에서 발견을 `F-n`으로 합치고 심각도를 매겨 사용자에게 보인다. 버린 목록(bandit 7건, B-관찰)도 함께 보인다(P6). 이 기록의 "완료"는 그때 사용자 확인으로 바꾼다
- 실행 중: 없음. 공격자 worktree 3개(`.claude/worktrees/agent-a54b…`, `agent-a601…`, `agent-a34f…`)는 커밋이 없어 병합하지 않는다
- 검증 주의: 이 worktree에는 실제 `.env`가 있다. A-1, A-2, A-4 재현은 `.env` 대신 가짜 파일을 읽게 하고 반출은 localhost로만 한다
- 사용자 대기: 없음
- 먼저 읽을 파일: 이 파일, 계획 3단계와 상단 "수정:" 줄

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 공격 예시 뺌 | 중심 영역 이름만 주고 예(`_socket` 등)는 주지 않았다(P4) | 계획 3단계 3번 표의 "예" 열 |

## 계획과 다른 점

- SKILL.md는 모든 공격자에게 같은 범위를 준다. 이 단계는 중심 영역을 나눴다(계획 3단계 3번에 적은 차이)
- 공격자 지시에서 예시를 뺐다(P4, 계획 "수정:" 줄)
- 결정적 도구(bandit, hypothesis, 샌드박스 소켓 시도)를 더한다(P5)

## 끝나는 조건 확인

- 조건: 검증된 발견 목록과 공격자별 버린 수가 기록됐다. 발견이 0이어도 끝난다.
- 결과: 충족(사용자 확인 전). 검증된 발견: A 7, B 5, C 5. 공격자별 버린 수: A 0, B 0(B-관찰은 설계가 정한 동작이라 발견이 아닌 관찰로 둠), C 0(C 자체 테스트 실패 6건은 환경 문제로 C가 뺐다). 지시 재현과 독립 발견 구분: 공격자에게 예시를 주지 않았으므로 17건 모두 독립 발견이다. 그중 A-2는 03 8장 기술 부채와 같은 내용이다
