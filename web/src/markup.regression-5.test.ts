// Regression test for ISSUE-007 (영·한 구절 매핑과 헷갈린 구절 목록에 마크다운 기호가 그대로 보인다), 06 QA 2026-11-06, docs/06-qa/output/qa-report.md
// 실행: web/에서 `node --test src/markup.regression-5.test.ts`.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { inlineParts } from './markup.ts'

test('구절의 인라인 코드와 굵게를 나눈다', () => {
  assert.deepEqual(inlineParts('which does **not** have `return_direct=True`'), [
    { kind: 'text', text: 'which does ' },
    { kind: 'strong', text: 'not' },
    { kind: 'text', text: ' have ' },
    { kind: 'inline', code: 'return_direct=True' },
  ])
})

test('한국어 구절도 같은 규칙이다', () => {
  assert.deepEqual(inlineParts('`return_direct=True`가 **없는** 도구'), [
    { kind: 'inline', code: 'return_direct=True' },
    { kind: 'text', text: '가 ' },
    { kind: 'strong', text: '없는' },
    { kind: 'text', text: ' 도구' },
  ])
})

test('구절 안에서는 코드 블록도 인라인 코드로 낸다(줄 안 요소라 <pre>를 넣지 않는다)', () => {
  const parts = inlineParts('see ```python\nx = 1\n``` here')
  assert.ok(parts.every((p) => p.kind !== 'block'))
  assert.deepEqual(parts.filter((p) => p.kind === 'inline'), [{ kind: 'inline', code: 'x = 1' }])
})

test('마크다운이 없으면 문자열 하나다', () => {
  assert.deepEqual(inlineParts('plain text'), [{ kind: 'text', text: 'plain text' }])
})
