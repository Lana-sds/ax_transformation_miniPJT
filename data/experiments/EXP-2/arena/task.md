# EXP-2 arena 과제 정의 (후보에게 주는 것)

작성: 2026-11-05. 후보 2개가 같은 이 과제를 받는다.

## 과제

LangChain 학습 퀴즈 앱의 생성 프롬프트를 고친 변형을 하나 만든다. 생성 모델은 공식 문서 스냅샷을 받아 문제 하나를 JSON으로 쓴다. 문제에는 근거 인용(`grounding_records[].quote`)이 들어간다.

인용 검사(`app/quiz/gates.py` `check_quote`)는 인용이 스냅샷 원문에 그대로 있는지 본다. NFKC 정규화와 공백 축약만 하고 마크다운 기호는 그대로 둔다. 03 단계에서 첫 시도 209번 중 116번이 인용 불일치(`quote_mismatch`)로 다시 만들어졌다. 확인한 원인 두 가지:

- 원문의 마크다운 링크 ``[`MessagesState`](/oss/python/langgraph/graph-api-state#messagesstate)``를 모델이 `` `MessagesState` ``로 벗겼다.
- 원문의 코드 펜스 첫 줄 ```` ```python theme={"theme":{...}} ````를 모델이 ```` ```python ````로 줄였다.

다른 원인(문장 일부 고쳐 쓰기, 생략, 표 행 다듬기 등)이 얼마나 되는지는 모른다.

변형 생성 프롬프트가 첫 시도에서 원문 그대로 복사한 인용을 더 많이 내게 한다. 문제 품질 규칙은 약하게 만들지 않는다.

## 고칠 수 있는 파일

`data/experiments/EXP-2/variants/control/`이 대조군이다(`packs/langchain/prompts/` 전체 사본). 이 중 다음만 고친다.

- `generate.md`: 생성 공통 지시. 자리표시자 `{{bucket}}`, `{{topic}}`, `{{format}}`, `{{question_type}}`, `{{pages}}`, `{{near_rule}}`, `{{format_rules}}`, `{{quality_rules}}`, `{{feedback}}`, `{{documents}}`를 그대로 둔다.
- `formats/*.md`, `quality/*.md`: 꼭 필요할 때만

Judge 파일(`judge.md`, `judge/`), `crosscheck.md`, `fakes.md`, `near.md`는 바꾸지 않는다.

## 지켜야 할 것

- 출력 스키마(`app/quiz/pipeline/schemas.py`)를 바꾸지 않는다.
- 문제 영어, 해설 한국어, 근거는 공식 문서 원문 인용뿐이라는 규칙을 유지한다.
- 품질 규칙 문구를 그대로 둔다. 테스트가 다음 문구를 찾는다: `Do not write a question that only asks to recall a definition`, `Each wrong choice must carry one plausible misconception`, `No cues`, `one paragraph per choice`, `why the canonical answer and every accepted answer are correct`, 그리고 `only`, `always`, `never`, `longer`. 남는 `{{`가 없어야 한다.
- 고친 파일 전체 길이(바이트)는 대조군 같은 파일 합의 1.3배 이하로 한다.
- 영어로 쓴다(대조군과 같다).

## 참고해도 되는 것

- 대조군 프롬프트 전체: `data/experiments/EXP-2/variants/control/`
- 코드: `app/quiz/pipeline/nodes.py`(생성 노드, 재생성 피드백 `QUOTE_HINT`), `app/quiz/gates.py`(인용 검사), `app/quiz/pipeline/schemas.py`
- 스냅샷 원문 예: `packs/langchain/snapshots/`(읽기만 한다. 바이트를 바꾸지 않는다)
- 설계: `docs/02-spec-design/output/design.md` 6장

## 보면 안 되는 것

- `data/quiz.db`, `data/experiments/EXP-2/slots.json`, `data/experiments/EXP-2/arena/` 안의 다른 후보 디렉토리, `docs/dev-process/04-prompt-model-experiments/`

## 낼 것

1. `data/experiments/EXP-2/variants/control/`을 `data/experiments/EXP-2/arena/candidate-<k>/prompts/`로 통째 복사한 뒤 위 파일만 고친다.
2. `data/experiments/EXP-2/arena/candidate-<k>/NOTES.md`: 바꾼 파일과 바꾼 이유를 원인별로 짧게 적는다. 대조군 대비 길이 비율을 적는다.
