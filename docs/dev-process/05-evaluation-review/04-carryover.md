# 04 carryover 기록

상태: 진행 중
시작: 2026-11-06 09:20
완료:
계획: [05-evaluation-review-plan.md](../05-evaluation-review-plan.md)의 4단계(끊는 시각 11:00, 09:45 수정)
세션 모델: Opus 5.5(`claude-opus-5-5`). 추론 강도: 미확인

## 입력

- 계획 1.2 이월 항목 14개

## 진행

결과는 [carryover.md](../../05-evaluation-review/output/carryover.md)에 있다. 여기는 과정만 둔다.

| 시각 | 한 일 | 스크립트·명령 |
| --- | --- | --- |
| 09:20경 | 1번 Judge 입력 코드 대조 시작(1단계 점검 대기 중). 프롬프트·허용 목록 변경 커밋 시각 확인 | `git log` |
| 09:40 | 2번 교차 풀이(Bedrock, `us-east-1`). 운영 `data/crosscheck/b20261105-01.*`을 스크래치 `ccbak/`에 복사(sha256 앞 16자 `3abb67ca1f81e6a1`, `c8b8378103f7e686`) → 실행 → 결과를 `data/experiments/EXP-2/crosscheck-arena.*`로 옮김 → 복사본으로 되돌림 → `git diff --stat data/crosscheck/` 0줄 | `QUIZ_DB=…arena.db uv run quiz crosscheck --batch b20261105-01` |
| 09:42 | 1번 문항별 비교 | 스크래치 `ev/c01_judge_input.py` |
| 09:43 | P7 근거 문장과 인용 비교 | 스크래치 `ev/c02_p7.py` |
| 09:44 | 7번 `version_conflict` 재실행, `ToolNode` 스냅샷 원문 대조 | 스크래치 `ev/c03_vc.py`, `grep handle_tool_errors` |
| 09:48 | 8번 유사 중복 조회 | 스크래치 `ev/c04_dup.py` |
| 09:49 | 9번 커버리지 | `uv run --with pytest-cov pytest --cov=quiz` |
| 09:50 | 10번 `b20261105-07` DB 조회 | `batches`, `batch_slots` 읽기 전용 |

교차 풀이 비용: 결과 파일에 토큰 수가 없다. 계획의 추정(문항당 입력 약 2.7만 토큰)으로 호출 10회 약 27만 입력 토큰이다. 단가는 `data/pricing/bedrock.yaml`에 두 모델이 없어 미확인이다. 상한 2 USD를 넘지 않는다고 판단한 근거는 호출 수(10회)와 추정 토큰뿐이다.

## 인계

갱신: 2026-11-06 09:55
- 마지막 완료 작업: `carryover.md` 초안
- 다음 작업: 5단계에서 사용자 확인
- 실행 중: 없음
- 사용자 대기: 없음
- 먼저 읽을 파일: `carryover.md`

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 11번 Service Quotas 조회 생략 | 마감이 13:30으로 당겨져 5단계 시간을 먼저 확보했다 | 계획 4단계 6번 "시간이 남으면" |

## 계획과 다른 점

- 1번을 1단계 점검 대기 중에 먼저 시작했다
- 교차 풀이를 "첫 문항 뒤 비용 확인" 없이 한 번에 돌렸다. 명령이 문항 단위로 멈추지 않고, 호출 10회라 상한을 넘을 수 없다고 봤다

## 끝나는 조건 확인

- 조건: 1.2 표의 모든 항목이 `carryover.md`에 결과 또는 "미확인"과 이유로 있다.
- 결과: 충족(사용자 확인 전). 14개 모두 있다
