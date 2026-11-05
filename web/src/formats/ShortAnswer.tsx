import type { FormatSpec } from './types'

// 단답. 입력 문자열 하나를 그대로 보낸다. 정규화와 허용 답안 비교는 서버가 한다(FR-3.2).
export const short: FormatSpec = {
  Input: ({ question, value, onChange, disabled }) => (
    <div className="short-answer">
      <label htmlFor={`${question.question_id}-short`}>답 입력</label>
      <input
        id={`${question.question_id}-short`}
        type="text"
        value={value[0] ?? ''}
        onChange={(e) => onChange([e.target.value])}
        disabled={disabled}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
      />
    </div>
  ),
  isComplete: (_q, value) => (value[0] ?? '').trim().length > 0,
}
