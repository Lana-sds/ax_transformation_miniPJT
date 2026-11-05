import { Markup } from '../MarkupText'
import { ChoiceList } from './ChoiceList'
import type { FormatSpec } from './types'

// 복수 선택. 고를 개수(select_count)를 보여 주고, 그 개수를 정확히 골라야 제출할 수 있다.
// 부분 점수는 없다(FR-3.1). select_count가 없으면 1개 이상이면 제출을 허용한다.
export const multi: FormatSpec = {
  Input: ({ question, value, onChange, disabled }) => {
    const n = question.select_count
    return (
      <>
        <p className="select-count">
          {n != null ? `${n}개를 고르세요` : '해당하는 보기를 모두 고르세요'}
          <span className="key">
            {' '}
            (선택 {value.length}
            {n != null ? `/${n}` : ''})
          </span>
        </p>
        <ChoiceList
          name={question.question_id}
          choices={question.choices ?? []}
          value={value}
          onChange={onChange}
          disabled={disabled}
          multiple
          maxSelect={n}
          renderBody={(c) => <Markup className="choice-text" text={c.text ?? ''} />}
        />
      </>
    )
  },
  isComplete: (q, value) => (q.select_count != null ? value.length === q.select_count : value.length > 0),
}
