import type { ReactNode } from 'react'
import type { Choice } from '../api'

type Props = {
  name: string
  choices: Choice[]
  value: string[]
  onChange: (value: string[]) => void
  disabled: boolean
  // true면 체크박스, 아니면 라디오다.
  multiple?: boolean
  // 복수 선택에서 이 개수를 채우면 고르지 않은 보기를 막는다.
  maxSelect?: number | null
  renderBody: (choice: Choice) => ReactNode
}

// 단일 선택, 복수 선택, 코드 선택이 같이 쓰는 보기 목록.
export function ChoiceList({ name, choices, value, onChange, disabled, multiple, maxSelect, renderBody }: Props) {
  const full = !!multiple && maxSelect != null && value.length >= maxSelect

  function toggle(id: string) {
    if (!multiple) {
      onChange([id])
      return
    }
    const next = value.includes(id) ? value.filter((v) => v !== id) : [...value, id]
    // 보기 순서대로 둔다.
    onChange(choices.map((c) => c.id).filter((cid) => next.includes(cid)))
  }

  return (
    <ul className="choices">
      {choices.map((c) => {
        const checked = value.includes(c.id)
        return (
          <li key={c.id}>
            <label className={checked ? 'chosen' : ''}>
              <input
                type={multiple ? 'checkbox' : 'radio'}
                name={name}
                value={c.id}
                checked={checked}
                disabled={disabled || (full && !checked)}
                onChange={() => toggle(c.id)}
              />
              <b>{c.id}.</b> {renderBody(c)}
            </label>
          </li>
        )
      })}
    </ul>
  )
}
