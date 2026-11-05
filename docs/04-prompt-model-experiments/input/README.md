# 04 입력

앞 단계 산출물은 복사하지 않고 링크한다.

| 입력 | 위치 | 쓰는 곳 |
| --- | --- | --- |
| 요구사항 | [requirements.md](../../01-requirements/output/requirements.md) NFR-4(모델), NFR-5(관측), 7.2(감사 기준), 7.3(기준선 지표) | 고정 조건, 지표, 모델 arm |
| 설계 | [design.md](../../02-spec-design/output/design.md) 12.0 | 파이프라인 노드 순서, 실패 이유, Judge 항목 |
| 구현 결과 | [implementation.md](../../03-implementation/output/implementation.md) 확정 1.0. 1.7 확인 항목, 7.3 기준선, 8장 기술 부채 | 실험 질문, 기준선 숫자 |
| 03 회고 | [10-retro.md](../../dev-process/03-implementation/10-retro.md) "다음 단계로 넘길 것" | 실험 후보 |
| 03 기록 | [04-m3.md](../../dev-process/03-implementation/04-m3.md) 파일럿 표, [05-m4.md](../../dev-process/03-implementation/05-m4.md) `quote_mismatch` 원인, [06-m5.md](../../dev-process/03-implementation/06-m5.md) 감사 메모와 교차 풀이 검토 | 기준선 숫자, 사람이 붙인 결함 라벨 |
| 프롬프트 | `packs/langchain/prompts/` | 변형의 출발점(대조군) |
| 실행 데이터 | `data/quiz.db`(git 제외), `data/crosscheck/*.json`, `data/metrics/baseline.json` | 기준선, 결함 문항, 정상 문항 |

2026-11-05 15:50 확인: 이 worktree에 `.env`와 `data/quiz.db`가 있다. 03은 `main`에 병합됐다(`f4758b3`).
