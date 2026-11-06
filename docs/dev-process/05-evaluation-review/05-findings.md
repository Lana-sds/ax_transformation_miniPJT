# 05 findings 기록

상태: 완료
시작: 2026-11-06 09:50
완료: 2026-11-06 10:25
계획: [05-evaluation-review-plan.md](../05-evaluation-review-plan.md)의 5단계(09:45 단축안: "높음"만 고친다)
세션 모델: Opus 5.5(`claude-opus-5-5`). 추론 강도: 미확인

## 입력

- 2단계 [acceptance.md](../../05-evaluation-review/output/acceptance.md), 3단계 [03-interrogate.md](03-interrogate.md), 4단계 [carryover.md](../../05-evaluation-review/output/carryover.md)

## 진행

- 09:50 [findings.md](../../05-evaluation-review/output/findings.md) 초안. F-1~F-19, 높음 5, 중간 9, 낮음 5. 공격자 발견 17건, 이월 4건, 사례 표 1건을 원인별로 합쳤다(A-1·A-3·A-4 → F-1, B-2·B-3 → F-10)

- 09:52 심각도별 목록, 버린 목록(bandit 7, ctypes 시도 1)을 사용자에게 보이고 물었다(P6)

| 질문 | 사용자 답 |
| --- | --- |
| "높음" 5개(F-1~F-5)를 모두 고칠까 | 5개 모두. 중간·낮음 14개는 `기록만` |
| F-1, F-2 수정 방식 | 파이썬 감사 훅(`sys.addaudithook`)으로 파일·네트워크(`_socket` 포함)·하위 프로세스·ctypes를 막고, 작업 폴더를 임시 폴더로, 자식 환경을 허용 목록으로 바꾼다. design.md 8.2 갱신 승인 |
| F-5로 풀에 있는 같은 인용 쌍 3개 | 그대로 두고 기록. 운영 DB를 바꾸지 않는다 |

- 09:53 워커 2개를 한 메시지에서 띄웠다. 기준 `f138ca59b652aedc0a2d19b0ffe4586c1fc30802`

| 워커 | 작업 | 소유 파일 |
| --- | --- | --- |
| W1 | F-1, F-2 | `sandbox/runner.py`, `sandbox/tests/*`, `app/quiz/sandbox_client.py`, `app/tests/test_sandbox_client.py` |
| W2 | F-3, F-4, F-5 | `app/quiz/batch.py`, `app/quiz/pool.py`, `app/quiz/pipeline/nodes.py`, `app/tests/` 안 해당 테스트 |

- 10:00 W2 보고. 브랜치 `worktree-agent-a00e49f3526d7c471` @ `d58da2413fcfa853990370394605d4af235452ff`. 바꾼 파일 `app/quiz/batch.py`, `app/quiz/pool.py`, `app/tests/test_batch.py`, `app/tests/test_pool.py`(새 파일). 새 테스트 5개(먼저 실패 확인). W2 전체 379 passed
  - F-3: `DONE`에 `audit_failed`를 더했다. 재개가 그 슬롯을 다시 만들지 않는다
  - F-4: `freeze`가 이미 있는 스냅샷 ID를 만들면 `created_at`을 지금으로, `rowid`를 맨 뒤로 옮긴다. `current_pool`이 늘 마지막 `freeze` 결과다
  - F-5: 그래프 실행 뒤 모듈 잠금 안에서 같은 버킷 passed를 DB에서 다시 읽어 중복을 다시 검사하고 저장까지 마친다. 모델 호출은 잠그지 않는다
  - W2가 남긴 점: 감사 뒤 다시 고정하기 전에는 현재 풀에 `audit_failed` 문제가 남는다(`sets.compose`가 상태를 보지 않음, 범위 밖). `pool_snapshots`에 명시적 정수 기본 키가 없어 VACUUM 뒤 같은 초 스냅샷 순서가 틀릴 수 있다
- 병합: W2 `worktree-agent-a00e49f3526d7c471` @ `d58da2413fcfa853990370394605d4af235452ff` → `66097c9`. `merge-base --is-ancestor f138ca5 d58da24` 통과. 병합 뒤 `uv run pytest -q` 379 passed
- 병합 뒤 재현 스크립트: C-1(`race.py 2`) passed 1개, 나머지 `dropped duplicate`, `[]`. C-2(`auditfail.py`) `unfinished() = 0`, 재개 뒤에도 `audit_failed 'Question alpha delta version 0'` 그대로, 다시 고정하면 새 스냅샷 `ps_c16445816275`(1문항). B-4(`probe_b4.py`) `current_pool -> ps_e9183e97416f`(A), `audit_failed question served in sets: 0`
- W2가 짚은 design.md 차이(승인 필요): 6.2 "passed·dropped가 아닌 슬롯만 다시 돈다" → `audit_failed`도 끝난 슬롯. 5.1 `pool_snapshots.created_at`은 마지막 고정 시각. "현재 풀 = 마지막으로 고정한 스냅샷" 정의 추가

- 10:08 W1 보고. 브랜치 `worktree-agent-ae5d1be703ce3bed1` @ `b59be43eb668f9e5d3156f86c37ad4593aaa0999`. 바꾼 파일 `sandbox/runner.py`, `sandbox/tests/test_runner.py`, `app/quiz/sandbox_client.py`, `app/tests/test_sandbox_client.py`. 새 테스트 샌드박스 16개, 앱 6개(먼저 실패 확인). 기존 `test_aws_and_langfuse_env_not_passed`의 기대(`QUIZ_KEEP_ME`가 넘어감)를 허용 목록 계약에 맞게 바꿨다. 경로 해석은 `os.path.realpath` 대신 `nt._getfullpathname`, `nt._getfinalpathname`을 쓴다(지시와 다른 점. 모델 코드가 `ntpath`를 바꿔도 판정이 안 바뀌게). `sqlite3`는 `:memory:`까지 막는다(`ATTACH`가 감사 이벤트 없이 파일을 연다)
- 병합: W1 `worktree-agent-ae5d1be703ce3bed1` @ `b59be43eb668f9e5d3156f86c37ad4593aaa0999` → `021aa87`. `merge-base --is-ancestor f138ca5 b59be43` 통과. 병합 뒤 앱 385 passed, 샌드박스 32 passed
- 병합 뒤 재현: 스크래치 `ev/v_a2.py`(실제 경로). A-1 `PermissionError` 2건, A-2 `NetworkBlockedError`, 리스너 수신 `[]`, A-3 자식 `QUIZ_DB` `None`, DB 쓰기 실패(`pwned` 테이블 없음), A-7 넘어간 변수 `[]`, A-5 손자 프로세스 `PermissionError` 0.7초, A-6 위조는 여전히 `{"ok": true, "stdout": "expected answer
"}`(F-6, 기록만). 스크래치 `ev/e02b_code.py`: 풀 코드형 11문항 44보기 실제 경로 재실행, 기대값 불일치 0, Judge 예측 불일치 0
- 10:12 W2 차이 3곳의 design.md 수정을 사용자에게 보이고 승인받았다. 승인된 8.2와 함께 design.md 15.0
- 10:15 `data/quiz.db` 행 수 0단계와 같다(13개 테이블 모두). sha256 `89fa897d…` 그대로
- F-7, F-8은 F-1 수정으로 재현이 막혀 `해당 없음`으로 바꿨다

- 10:20 06 사전 QA 입력(`docs/06-qa/input/pre-qa-findings.md`, 보조 세션 작성)을 읽었다. 이 파일은 코디네이터 커밋 `d492c0a`에 함께 들어갔다(의도하지 않음, 06 입력 위치라 그대로 둔다). Q-1("새 세트" 두 번)은 F-10과 같다. Q-3(정답 위치 쏠림)은 평가 풀에서 확인했다: 단일 14/18, 코드 11/11, 복수 13/14가 A. F-20(중간, 기록만)으로 올렸다. 등급을 묻는 질문은 사용자가 거절했다. 계획 1.3 기준대로 중간으로 둔다. Q-2(지난 세트에 묶인 화면)는 06 몫이다

## 인계

갱신: 2026-11-06 10:17
- 마지막 완료 작업: W1, W2 병합과 확인, design.md 15.0, 행 수 대조
- 다음 작업: 사용자에게 단계 완료를 확인받고 `doc` 모드로 간다
- 실행 중: 없음
- 사용자 대기: 없음
- 먼저 읽을 파일: `findings.md`

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 수정 범위 | F-1~F-5 수정, F-6~F-19 기록만 | 계획 결정 3(09:45 단축안으로 "높음"만) |
| 샌드박스 방식 | 감사 훅 + 임시 작업 폴더 + 환경 허용 목록. design.md 8.2를 고친다 | design.md 8.2 값(사용자 승인 09:52) |
| 풀의 중복 쌍 3개 | 데이터는 그대로 둔다 | 없음 |
| W2 수정의 설계 반영 | 6.2 재개 대상, 6.2 동시 슬롯 중복 재검사, 5.2 현재 풀 정의. 사용자 승인 10:12 | design.md 6.2, 5.2 → 15.0 |
| 제출 PR에 `data/quiz.db` 포함 | 평가받은 DB(sha256 `89fa897d…`)를 커밋한다. `.gitignore`에 `!data/quiz.db`. 커밋 전 비밀 문자열 검사(텍스트 칸 5,468개, AWS 키 형식·`aws_secret_access_key`·Langfuse 키 접두사·`.env` 형식 줄·Bearer 토큰) 0건. 사용자 승인 10:03 | design.md 4.1(`*.db`로 커밋 안 함) → 14.0 |

## 계획과 다른 점

- 없음

## 끝나는 조건 확인

- 조건: 모든 `F-n`에 상태가 있다. 전체 테스트가 통과한다. `data/quiz.db` 행 수가 0단계와 같다.
- 결과: 충족(사용자 확인 2026-11-06 10:25, "docs 완료" 지시). F-1~F-20 모두 조치 값이 있다(수정 5, 해당 없음 2, 기록만 13). 앱 385 passed, 샌드박스 32 passed. `data/quiz.db` 행 수 0단계와 같다
