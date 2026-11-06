# 02 fix 기록

상태: 완료
시작: 2026-11-06 11:26
작업 끝: 2026-11-06 11:48
완료: 2026-11-06 12:55
계획: [06-qa-plan.md](../06-qa-plan.md)의 2단계
세션 모델: claude-opus-5-5. 추론 강도는 세션 안에서 읽지 못하므로 적지 않는다

## 입력

- [01-qa.md](01-qa.md) DEF 목록. 결정 2(화면 코드로 고칠 수 있는 버그는 모두 고친다), IMP-1·IMP-2(사용자 결정)
- 사용자 지시(11:27): 화면 수정은 워커 W1 하나로 지금 띄운다. 병합은 브라우저 시험과 기준 건강 점수 뒤에 한다

## 진행

- 11:26 W1을 격리 worktree로 띄웠다. 기준 `b34d5d2ca59edb2d17d546ec770e8e553eb456e5`. 넘긴 것: ISSUE-001~004(= DEF-1~4), IMP-1·IMP-2. 넘기기 전에 DEF-3, DEF-4를 두 번째로 재현했다(probe 039, 040).
- 11:33 DEF-5를 확정하고 W1에 ISSUE-005로 더했다.
- W1 보고: 커밋 6개, `npm run build` 통과, `node --test src/*.test.ts` 31 통과, `uv run pytest -q` 385 통과. W1 worktree에 샌드박스 환경이 없어 첫 pytest에서 11개가 `SandboxNotReady`로 실패했고, `uv sync --project sandbox --frozen` 뒤 통과했다(추적 파일 변경 없음). `oxlint` 경고 1개(`set-state-in-effect`, `App.tsx` 84행)는 기준 커밋에 이미 있었다.
- 병합: W1 `worktree-agent-a1d420c3d55017e4f` @ `cc4013f3b40f5ed36e44db800227a67e0517ce4a` → `c0f282d933e197ce8da6acffc52283e9142d7509`. 병합 전 `git merge-base --is-ancestor b34d5d2 cc4013f` 통과.
- 11:45 3단계 재확인 중에 DEF-7(구절 매핑 표와 헷갈린 구절 목록의 마크다운 기호)을 찾았다. 두 문제에서 재현했다(세트 10 4번, 세트 1 6번). 코디네이터가 직접 고쳤다. 테스트를 먼저 써서 실패(`does not provide an export named 'inlineParts'`)를 본 뒤 구현했다.

| DEF | ISSUE | 커밋 | 바꾼 파일 | 회귀 테스트 | 판정 |
| --- | --- | --- | --- | --- | --- |
| DEF-1 | ISSUE-001 | `229b84e` | `App.tsx`, `TagForm.tsx`, `singleFlight.ts` | `singleFlight.regression-1.test.ts` | verified |
| DEF-2 | ISSUE-002 | `9b35bd6` | `App.tsx`, `conflict.ts` | `conflict.regression-2.test.ts` | verified |
| DEF-3 | ISSUE-003 | `aba9dc6` | `App.tsx`, `particle.ts` | `particle.regression-3.test.ts` | verified |
| DEF-4 | ISSUE-004 | `b9a8a2e` | `markup.ts`, `MarkupText.tsx` | `markup.regression-4.test.ts` | verified |
| DEF-5 | ISSUE-005 | `cc4013f` | `index.css` | 없음(CSS만). 브라우저 수치로 확인 | verified |
| IMP-1, IMP-2 | - | `43ae78a` | `App.tsx`, `tooltips.ts`, `index.css` | `tooltips.test.ts` | verified |
| DEF-7 | ISSUE-007 | `86d1a22` | `markup.ts`, `MarkupText.tsx`, `Evidence.tsx`, `TagForm.tsx` | `markup.regression-5.test.ts` | verified |
| DEF-6 | - | - | - | - | 기록만(결정 2) |

진행 점검(gstack, 수정 5개마다): 수정 7개, 되돌림 0, 관련 없는 파일 수정 0. 계속 조건을 만족했다.

## 인계

갱신: 2026-11-06 11:55
- 마지막 완료 작업: DEF-1~5, DEF-7, IMP-1·IMP-2 수정과 병합
- 다음 작업: 사용자 확인, `doc`
- 실행 중: API 8002, 웹 5175(이 세션 백그라운드)
- 사용자 대기: 없음(1~3단계 확인 2026-11-06 12:55)
- 먼저 읽을 파일: [03-verify.md](03-verify.md)

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 병렬 수정 | W1이 1단계와 동시에 고쳤다(사용자 지시 11:27) | gstack 순서(발견 보고 뒤 수정). 계획 "수정:" 줄 |
| DEF-7 직접 수정 | W1이 끝난 뒤 찾아 코디네이터가 고쳤다 | 없음 |
| 근거 인용 | `**`, 백틱을 원문 그대로 둔다 | 없음(공식 문서 원문 인용 규칙) |

## 계획과 다른 점

- 3장 병렬 표는 코디네이터 한 줄이었다. W1 줄로 고쳤다(계획 "수정:" 11:27)

## 옮긴 과정 기록
