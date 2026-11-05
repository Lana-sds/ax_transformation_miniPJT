import { FORMATS } from './registry'
import type { FormatInputProps } from './types'

// 문제 형식에 맞는 입력 컴포넌트를 고른다. 모르는 형식은 제출할 수 없게 안내만 한다.
export function AnswerInput(props: FormatInputProps) {
  const spec = FORMATS[props.question.format]
  if (!spec) return <p className="error">지원하지 않는 형식: {props.question.format}</p>
  return <spec.Input {...props} />
}
