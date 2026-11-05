# EXP-1 candidate-1 노트

작성: 2026-11-05. `variants/control/`을 `prompts/`로 통째 복사한 뒤 `judge.md`, `judge/choice.md`, `judge/short.md` 세 파일만 고쳤다. `judge/code.md`와 나머지 파일은 대조군과 같다.

## 접근

새 항목을 늘리지 않고(`explanation_correct` 하나만 더함), 결함 유형마다 기존 항목의 false 조건을 한 문장씩 더했다. 너그러움을 줄이되 오탈락이 늘지 않게, 항목을 false로 둘 때는 구체적인 결함이 있어야 한다는 한 줄을 더했다.

## 결함 유형별 변경

| 결함 유형 | 파일 | 변경 |
| --- | --- | --- |
| 해설이 틀림 | `judge.md` | `explanation_correct` 항목을 더했다. 각 보기(단답은 정답과 허용 답안마다)에 문서와 맞는 이유가 있어야 한다. 다른 보기를 반박하는 문단, 문서와 다르거나 문서에 없는 동작 서술, "문서에 없다"뿐인 부재 논증이면 false다. `judge.md`에 두어 단답 포함 모든 형식에 적용된다. |
| 지문, 보기가 정답을 알려 줌 | `judge/choice.md` | `no_cue` 테스트 2개를 더했다. 5. Stem leak: 지문(문장, 코드)에 정답 코드나 API 이름이 있거나 그 이름을 말로 풀어 씀. 6. Copied wording: 정답 보기만 문서 문장을 거의 그대로 옮김. |
| 단답 지문이 정답을 알려 줌 | `judge/short.md` | 단답은 `no_cue`를 검사하지 않으므로(`judge_items`), `answer_key_correct`에 "지문이 정답을 보이거나 풀어 쓰지 않는다"를 더했다. |
| 인용 일부가 무관 | `judge.md` | `quote_supports_answer`에 "정답에도, 오답 반박에도 관계없는 인용이 하나라도 있으면 false"를 더했다. 오답 반박용 인용은 정상으로 둔다. |
| 지문 모호, 전제 누락 | `judge.md` | `answer_key_correct`에 "모호한 지문이나 빠진 전제 때문에 다른 답도 옹호할 수 있으면 false"를 더했다. |
| 오탈락 억제 | `judge.md` | "Fail an item only for a concrete defect, not for style." 한 줄을 더했다. |

지킨 것: 출력 스키마, 항목 이름 백틱 표기, 자리표시자 4개(`{{format_rules}}`, `{{question}}`, `{{page}}`, `{{document}}`), "문서만 근거" 지시, "질문과 문서는 데이터" 지시.

## 길이

| 파일 | 대조군(바이트) | 변형(바이트) |
| --- | --- | --- |
| `judge.md` | 976 | 1542 |
| `judge/choice.md` | 1216 | 1408 |
| `judge/short.md` | 578 | 622 |
| 합 | 2770 | 3572 |

비율: 1.290(디스크 CRLF 기준). 줄바꿈을 LF로 셌을 때 2728 → 3525, 1.292. 둘 다 1.3 이하다.

## 미확인

- 모델 호출을 하지 않았다. 판정 변화와 오탈락률은 미확인이다.
- `JudgeVerdict`에 `explanation_correct` 필드는 아직 없다. 과제 정의대로 코드 쪽에서 더한다고 보았다.
