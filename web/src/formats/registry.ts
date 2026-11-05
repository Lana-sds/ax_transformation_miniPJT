import type { PublicQuestion } from '../api'
import { code } from './CodeChoice'
import { multi } from './MultiChoice'
import { short } from './ShortAnswer'
import { single } from './SingleChoice'
import type { FormatSpec } from './types'

// 형식 레지스트리. 새 형식은 여기에 컴포넌트를 더한다(NFR-1.2).
export const FORMATS: Record<string, FormatSpec> = { single, multi, short, code }

export function isAnswerComplete(question: PublicQuestion, value: string[]): boolean {
  const spec = FORMATS[question.format]
  return !!spec && spec.isComplete(question, value)
}
