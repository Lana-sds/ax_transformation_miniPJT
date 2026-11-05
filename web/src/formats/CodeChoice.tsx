import { ChoiceList } from './ChoiceList'
import type { FormatSpec } from './types'

// 코드 선택. 보기마다 코드 블록을 보여 준다. "코드 보기" 링크(doc_url)는 답을 낸 뒤 결과 화면에 나온다.
// 답 제출 전 응답에 doc_url이 없기 때문이다(design.md 7.1, 8.5).
export const code: FormatSpec = {
  Input: ({ question, value, onChange, disabled }) => (
    <ChoiceList
      name={question.question_id}
      choices={question.choices ?? []}
      value={value}
      onChange={onChange}
      disabled={disabled}
      renderBody={(c) => (
        <pre className="code-block">
          <code>{c.code ?? c.text}</code>
        </pre>
      )}
    />
  ),
  isComplete: (_q, value) => value.length === 1,
}
