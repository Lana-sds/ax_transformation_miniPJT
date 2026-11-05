# 04 입력

앞 단계 산출물은 복사하지 않고 링크한다.

| 입력 | 위치 | 쓰는 곳 |
| --- | --- | --- |
| 요구사항 | [requirements.md](../../01-requirements/output/requirements.md) NFR-4(모델), NFR-5(관측), 7.3(기준선 지표) | 고정 조건, 지표 |
| 설계 | [design.md](../../02-spec-design/output/design.md) | 파이프라인 노드 순서, 실패 이유 |
| 03 산출물 | [03-implementation/output/](../../03-implementation/output/) | 실행 순서([m0-smoke.md](../../03-implementation/output/m0-smoke.md)) |
| 03 기록 | [04-m3.md](../../dev-process/03-implementation/04-m3.md) 파일럿 표, [06-m5.md](../../dev-process/03-implementation/06-m5.md) 교차 풀이 검토 | 기준선 숫자 |
| 프롬프트 | `packs/langchain/prompts/` | 변형의 출발점(대조군) |
| 실행 데이터 | `data/quiz.db`(git 제외), `data/crosscheck/*.json` | 기준선, 결함 문항 |
| 기준선 지표 | `data/metrics/baseline.json`(03 T6.1이 만든다. 2026-11-05 현재 없음) | 대조군 지표 |

03 단계는 2026-11-05 현재 진행 중이다(M5~M7 남음). 최종 문서 `implementation.md`는 아직 없다.
