# 05 입력

앞 단계 산출물은 복사하지 않고 링크한다.

| 입력 | 위치 | 쓰는 곳 |
| --- | --- | --- |
| 요구사항 | [requirements.md](../../01-requirements/output/requirements.md) 3.0. 완료 조건, 기준선 지표, 제약 C-1 | 평가 기준, 마감 |
| 설계 | [design.md](../../02-spec-design/output/design.md) 13.0 | 구현 값 대조, 리뷰 범위 |
| 수용 기준 | [seed.yaml](../../02-spec-design/output/seed.yaml) 1.1.0. 수용 기준 9개 | 수용 기준 검증 |
| 구현 결과 | [implementation.md](../../03-implementation/output/implementation.md) 확정 1.0. 1.7 확인 항목, 7장 완료 조건 판정, 8장 기술 부채 | 기준선 판정, 이월 항목 |
| MVP 점검표 | [mvp-checklist.md](../../03-implementation/output/mvp-checklist.md) | 완료 조건 측정 쿼리 |
| 실험 결과 | [experiments.md](../../04-prompt-model-experiments/output/experiments.md) 확정 1.0. 1.8 확인 항목 8개 | 품질 지표, 이월 항목 |
| 03 회고 | [10-retro.md](../../dev-process/03-implementation/10-retro.md) "다음 단계로 넘길 것" | Seed QA 2차 지적 6개, 샌드박스 네트워크 차단 |
| 04 회고 | [07-retro.md](../../dev-process/04-prompt-model-experiments/07-retro.md) "다음 단계로 넘길 것" | 이월 항목 |
| 코드 | `app/`, `web/`, `sandbox/`, `packs/langchain/` | 수용 기준 검증, 적대적 리뷰 |
| 실행 데이터 | `data/quiz.db`(git 제외), `data/metrics/baseline.json`, `data/crosscheck/`, `data/experiments/`(`*.db`는 git 제외) | 완료 조건 쿼리, 품질 지표 |

2026-11-06 09:00 확인: 이 worktree에는 `.env`, `data/quiz.db`, `data/experiments/EXP-2/*.db`, `app/.venv`, `sandbox/.venv`, `web/node_modules`가 없다. 04 worktree(`04-prompt-model-experiments`)에는 `.env`, `data/quiz.db`, `data/experiments/EXP-2/arena.db`, `control.db`가 있다. 계획 0단계에서 복사하고 설치한다.
