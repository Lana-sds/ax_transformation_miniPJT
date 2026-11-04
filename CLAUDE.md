# ax_transformation_miniPJT

LLM 학습 문제 풀이 웹앱 과제. LangChain 팩을 먼저 만들고 CCA-F 팩은 다음에 붙인다.

## 기준 문서
- 요구사항: `docs/01-requirements/output/requirements.md`
- 구현 값: `docs/02-spec-design/output/design.md`
- 수용 기준: `docs/02-spec-design/output/seed.yaml`
- 작업 단위 요약: `SERVICE.md`(PRD). 새 요구사항을 더하지 않는다.
- 문서끼리 다르면 요구사항 정의서가 우선한다. 구현 값은 설계서를 따른다.

## 디렉토리
- `docs/NN-<stage>/`: 단계별 과제 결과물. 단계는 docs/dev-process/skillset-by-lifecycle.md를 따른다.
  - `input/`: 이 단계의 입력. 앞 단계 output은 복사하지 말고 링크한다.
  - `output/`: 이 단계의 산출물. 다음 단계의 input이 된다.
- `docs/dev-process/`: 개발 과정 문서. 도구 선택 기준, 단계별 실행 계획(`NN-<stage>-plan.md`), 수행 기록(`NN-<stage>/`).
- 코드는 docs/ 밖에 둔다. Python 앱은 `app/`(uv 프로젝트, 실행은 `app/`에서 `uv run quiz ...`), LangChain 전용 데이터·프롬프트는 `packs/langchain/`. 구조는 `design.md` 4.1을 따른다.

## 고정 결정
- 모델 호출은 AWS Bedrock 경유로 쓴다. Anthropic API 직접 호출 안 함. 사용 가능 모델은 `docs/01-requirements/input/bedrock-model-list.md`를 따른다(Claude, Amazon Nova).
- 정답·해설 근거는 공식 문서 원문 인용만 인정. 학습 노트는 탐색용.
- 문제는 영어, 해설은 한국어. 형식: 단일·복수 선택, 단답, 코드 선택.
