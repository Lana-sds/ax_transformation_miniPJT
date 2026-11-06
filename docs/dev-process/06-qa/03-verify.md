# 03 verify 기록

상태: 완료
시작: 2026-11-06 11:41
작업 끝: 2026-11-06 11:55
완료: 2026-11-06 12:55
계획: [06-qa-plan.md](../06-qa-plan.md)의 3단계
세션 모델: claude-opus-5-5. 추론 강도는 세션 안에서 읽지 못하므로 적지 않는다

## 입력

- 병합 커밋 `c0f282d`, DEF-7 수정 `86d1a22`
- 1단계 재현 절차([01-qa.md](01-qa.md))

## 진행

### 명령 재실행(superpowers 검증 절차)

| 주장 | 명령 | 결과 |
| --- | --- | --- |
| 앱 테스트 통과 | `app/`에서 `uv run pytest -q` | `385 passed, 13 warnings`(병합 뒤, DEF-7 뒤 두 번) |
| 웹 테스트 통과 | `web/`에서 `node --test src/*.test.ts` | tests 35, pass 35, fail 0 |
| 빌드 | `web/`에서 `npm run build` | `✓ built`(tsc -b 포함) |
| 제출 DB 보호 | `sha256sum data/quiz.db` | `89fa897d…bbde`, 0단계와 같다. 행 수 117/3/10/41 같다. `git status` 변경 없음 |

### 회귀 테스트 빨강-초록

| 테스트 | 빨강 | 초록 |
| --- | --- | --- |
| `markup.regression-4` | 수정 전 `markup.ts`(`b34d5d2`)로 바꿔 pass 3, fail 4 | 되돌려 pass 7, fail 0 |
| `conflict.regression-2` | `set_closed` 조건을 `false`로 바꿔 pass 3, fail 1 | pass 4, fail 0 |
| `particle.regression-3` | 을/를 분기를 늘 '를'로 바꿔 pass 1, fail 1 | pass 2, fail 0 |
| `singleFlight.regression-1` | 잠금(`pending = true`)을 빼서 pass 2, fail 1 | pass 3, fail 0 |
| `markup.regression-5` | 구현 전 `inlineParts` 없음으로 fail 1 | pass 4, fail 0 |

### 브라우저 재확인(처음 재현 절차 그대로)

| DEF | 절차 | 결과 | 스크린샷 |
| --- | --- | --- | --- |
| DEF-1 | 세트 10 끝 화면에서 콘솔로 같은 틱 두 번 클릭 | `POST /api/sets` 1번(200), 세트 12가 열림, 오류 문구 없음 | `after-def-1.jpg` |
| DEF-2 | 화면이 세트 12, 다른 클라이언트가 세트 13 생성, 화면에서 답 제출 | `409 set_closed` 뒤 "이 세트는 닫혔다. 새 세트를 시작한다."와 "새 세트 시작". 저장소 값이 비고, 새로고침해도 첫 화면이다. 버튼으로 세트 14가 열림 | `after-def-2.jpg` |
| DEF-3 | 세트 10 끝 화면 | "세트 10을 다 풀었다.", "세트 1을 다 풀었다." | `after-def-3.jpg` |
| DEF-4 | 세트 10 4번 결과 | 본문·해설 `<strong>` 표시. 근거 인용의 `**` 4개는 원문 그대로 | `after-def-4.jpg` |
| DEF-5 | 375×812, 세트 1의 8번, 10번, 1번 | `scrollWidth` 360(전 574, 629) | 없음(모바일 에뮬레이션에서 빈 화면으로 찍힘) |
| DEF-7 | 세트 1 6번, 세트 10 4번 결과의 구절 매핑 표 | 원시 기호 칸 0, 인라인 코드 8개, 굵게 2개(`not`, `없는`). 태그 화면 구절 목록 원시 기호 0 | `after-def-7.jpg`, `after-def-7-tagform.jpg` |
| IMP-1 | "세트 14"에 마우스, Tab 1번 | 두 경우 모두 말풍선 visible | `after-imp-1-hover.jpg` |
| IMP-2 | "감사"에 마우스, Tab 2번 | 두 경우 모두 말풍선 visible. 다른 쪽은 hidden | `after-imp-2-hover.jpg` |

### 건강 점수(같은 범위: Console, Links, Visual, Functional, UX, Content)

| 범주 | 전 | 후 |
| --- | --- | --- |
| Console | 100 | 100 |
| Links | 100 | 100 |
| Visual | 92 | 100 |
| Functional | 69 | 92(DEF-6 기록만) |
| UX | 100 | 100 |
| Content | 94 | 100 |
| 점수 | 90 | 98 |

후 값은 [after.json](../../06-qa/output/after.json)이다. 기준에는 3단계에서 찾은 DEF-7이 빠져 있다. 넣어도 기준은 90(90.07)이다. 성능과 접근성은 시험하지 않아 둘 다 잠정값이다.

## 인계

갱신: 2026-11-06 11:55
- 마지막 완료 작업: 3단계 재확인
- 다음 작업: 사용자 확인 뒤 `doc`(`docs/06-qa/output/qa-report.md`)
- 실행 중: API 8002(`QUIZ_DB=data/experiments/qa06.db`), 웹 5175
- 사용자 대기: 없음(1~3단계 확인 2026-11-06 12:55)
- 먼저 읽을 파일: 이 파일, [01-qa.md](01-qa.md), [02-fix.md](02-fix.md)

## 결정

| 결정 | 내용 | 바뀐 기존 결정 |
| --- | --- | --- |
| 기준 점수 | 덮어쓰지 않고 차이를 적는다 | 없음(gstack "보고서를 덮어쓰지 않는다") |

## 계획과 다른 점

- 없음

## 옮긴 과정 기록
