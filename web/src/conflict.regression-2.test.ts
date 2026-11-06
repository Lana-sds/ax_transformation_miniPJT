// Regression test for ISSUE-002 (닫힌 세트에서 화면이 멈춘다), 06 QA 2026-11-06, docs/06-qa/output/qa-report.md
// 실행: web/에서 `node --test src/conflict.regression-2.test.ts`.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { conflictAction, SET_CLOSED_NOTICE } from './conflict.ts'

test('set_closed면 세트를 비우고 새 세트를 시작하게 한다', () => {
  assert.deepEqual(conflictAction({ reason: 'set_closed', set_id: 's002-x' }, 's002-x'), {
    kind: 'closed',
    notice: SET_CLOSED_NOTICE,
  })
  assert.equal(SET_CLOSED_NOTICE, '이 세트는 닫혔다. 새 세트를 시작한다.')
})

test('untagged_wrong이면 그 세트를 다시 불러 태그 입력으로 보낸다', () => {
  assert.deepEqual(conflictAction({ reason: 'untagged_wrong', set_id: 's001-a' }, null), {
    kind: 'reload',
    setId: 's001-a',
    notice: '태그 없는 오답이 있다. 태그를 저장한 뒤 계속한다.',
  })
})

test('already_answered면 지금 세트를 다시 불러온다', () => {
  assert.deepEqual(conflictAction({ reason: 'already_answered' }, 's003-b'), {
    kind: 'reload',
    setId: 's003-b',
    notice: null,
  })
  assert.deepEqual(conflictAction({ reason: 'already_answered' }, null), { kind: 'none' })
})

test('모르는 이유나 409가 아니면 아무것도 하지 않는다', () => {
  assert.deepEqual(conflictAction({ reason: 'something_else' }, 's003-b'), { kind: 'none' })
  assert.deepEqual(conflictAction(null, 's003-b'), { kind: 'none' })
  assert.deepEqual(conflictAction({ reason: 'untagged_wrong' }, 's003-b'), { kind: 'none' })
})
