# 05 findings 기록

상태: 진행 중
시작: 2026-11-06 09:50
완료:
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

## 인계

갱신: 2026-11-06 09:54
- 마지막 완료 작업: 고칠 목록 확인, 워커 띄움
- 다음 작업: 워커 결과를 `git merge-base --is-ancestor f138ca5 <해시>`로 확인하고 병합한다. 병합 뒤 전체 테스트, E2(코드형 44보기 재실행), 공격자 재현 스크립트를 다시 돌린다. design.md 8.2를 고친다(승인됨). `data/quiz.db` 행 수를 다시 센다
- 실행 중: W1: F-1, F-2, 기준 f138ca59b652aedc0a2d19b0ffe4586c1fc30802
- 사용자 대기: 없음
- 먼저 읽을 파일: `findings.md`

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 수정 범위 | F-1~F-5 수정, F-6~F-19 기록만 | 계획 결정 3(09:45 단축안으로 "높음"만) |
| 샌드박스 방식 | 감사 훅 + 임시 작업 폴더 + 환경 허용 목록. design.md 8.2를 고친다 | design.md 8.2 값(사용자 승인 09:52) |
| 풀의 중복 쌍 3개 | 데이터는 그대로 둔다 | 없음 |
| 제출 PR에 `data/quiz.db` 포함 | 평가받은 DB(sha256 `89fa897d…`)를 커밋한다. `.gitignore`에 `!data/quiz.db`. 커밋 전 비밀 문자열 검사(텍스트 칸 5,468개, AWS 키 형식·`aws_secret_access_key`·Langfuse 키 접두사·`.env` 형식 줄·Bearer 토큰) 0건. 사용자 승인 10:03 | design.md 4.1(`*.db`로 커밋 안 함) → 14.0 |

## 계획과 다른 점

- 없음

## 끝나는 조건 확인

- 조건: 모든 `F-n`에 상태가 있다. 전체 테스트가 통과한다. `data/quiz.db` 행 수가 0단계와 같다.
- 결과: 미확인(진행 중)
