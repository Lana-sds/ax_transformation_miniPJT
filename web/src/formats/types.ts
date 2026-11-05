import type { ComponentType } from 'react'
import type { PublicQuestion } from '../api'

// 형식 컴포넌트 공통 계약(design.md 5.2: 형식 추가는 채점 함수 등록과 UI 컴포넌트 추가로 한다).
// 답은 항상 문자열 배열이다. 선택형은 보기 ID, 단답은 입력 문자열 하나다.
export type FormatInputProps = {
  question: PublicQuestion
  value: string[]
  onChange: (value: string[]) => void
  disabled: boolean
}

export type FormatSpec = {
  Input: ComponentType<FormatInputProps>
  // 제출 버튼을 켤 수 있는 답인지 본다. 채점은 서버가 한다.
  isComplete: (question: PublicQuestion, value: string[]) => boolean
}
