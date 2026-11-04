# ax_transformation_miniPJT

LLM 학습 문제 풀이 웹앱 과제. 후보 2개(CCA-F, LangChain) 중 선택 진행 중.

## 디렉토리
- `docs/NN-<stage>/`: 단계별 과제 결과물. 단계는 docs/dev-process/skillset-by-lifecycle.md를 따른다.
  - `input/`: 이 단계의 입력. 앞 단계 output은 복사하지 말고 링크한다.
  - `output/`: 이 단계의 산출물. 다음 단계의 input이 된다.
- `docs/dev-process/`: 개발 과정 문서. 도구 선택 기준, 단계별 실행 계획(`NN-<stage>-plan.md`), 수행 기록(`NN-<stage>/`).
- 코드는 docs/ 밖에 둔다.

## 고정 결정
- 모델 호출은 "Bedrock 경유 Claude"로 쓴다. Anthropic API 직접 호출 안 함.
- 정답·해설 근거는 공식 문서 원문 인용만 인정. 학습 노트는 탐색용.
- 문제는 영어, 해설은 한국어. 형식: 단일·복수 선택, 단답, 코드 선택.
