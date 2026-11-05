import { Markup } from '../MarkupText'
import { ChoiceList } from './ChoiceList'
import type { FormatSpec } from './types'

export const single: FormatSpec = {
  Input: ({ question, value, onChange, disabled }) => (
    <ChoiceList
      name={question.question_id}
      choices={question.choices ?? []}
      value={value}
      onChange={onChange}
      disabled={disabled}
      renderBody={(c) => <Markup className="choice-text" text={c.text ?? ''} />}
    />
  ),
  isComplete: (_q, value) => value.length === 1,
}
