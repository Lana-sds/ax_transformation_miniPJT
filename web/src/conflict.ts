import type { ConflictDetail } from './api'

// 409 detail의 reason을 화면 동작으로 바꾼다(D-h). JSX가 없어 node --test로 바로 시험한다.
// untagged_wrong: 그 세트를 다시 불러 태그 입력으로 보낸다.
// already_answered: 지금 세트를 다시 불러 저장된 결과를 보인다.
// set_closed: 다른 곳에서 새 세트가 시작돼 이 세트가 닫혔다. 세트를 비우고 새 세트 시작을 보인다(ISSUE-002).

export const SET_CLOSED_NOTICE = '이 세트는 닫혔다. 새 세트를 시작한다.'

export type ConflictAction =
  | { kind: 'reload'; setId: string; notice: string | null }
  | { kind: 'closed'; notice: string }
  | { kind: 'none' }

export function conflictAction(c: ConflictDetail | null, currentSetId: string | null): ConflictAction {
  if (c?.reason === 'untagged_wrong' && c.set_id)
    return { kind: 'reload', setId: c.set_id, notice: '태그 없는 오답이 있다. 태그를 저장한 뒤 계속한다.' }
  if (c?.reason === 'already_answered' && currentSetId)
    return { kind: 'reload', setId: currentSetId, notice: null }
  if (c?.reason === 'set_closed') return { kind: 'closed', notice: SET_CLOSED_NOTICE }
  return { kind: 'none' }
}
