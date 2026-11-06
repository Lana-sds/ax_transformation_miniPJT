// Regression test for ISSUE-004 (마크다운 굵게가 별표 그대로 보인다), 06 QA 2026-11-06, docs/06-qa/output/qa-report.md
// 실행: web/에서 `node --test src/markup.regression-4.test.ts`.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { parseMarkup } from './markup.ts'

test('문제 문장의 **굵게**를 나눈다', () => {
  assert.deepEqual(parseMarkup('which does **not** have return_direct=True'), [
    { kind: 'text', text: 'which does ' },
    { kind: 'strong', text: 'not' },
    { kind: 'text', text: ' have return_direct=True' },
  ])
})

test('해설 첫머리의 **정답.**을 나눈다', () => {
  assert.deepEqual(parseMarkup('A. **정답.** 문서의 설명'), [
    { kind: 'text', text: 'A. ' },
    { kind: 'strong', text: '정답.' },
    { kind: 'text', text: ' 문서의 설명' },
  ])
})

test('한 문장에 굵게가 여러 개면 모두 나눈다', () => {
  assert.deepEqual(parseMarkup('**A**와 **B**'), [
    { kind: 'strong', text: 'A' },
    { kind: 'text', text: '와 ' },
    { kind: 'strong', text: 'B' },
  ])
})

test('인라인 코드 안의 **는 굵게로 나누지 않는다', () => {
  assert.deepEqual(parseMarkup('Use `**kwargs` and **this**.'), [
    { kind: 'text', text: 'Use ' },
    { kind: 'inline', code: '**kwargs' },
    { kind: 'text', text: ' and ' },
    { kind: 'strong', text: 'this' },
    { kind: 'text', text: '.' },
  ])
  assert.deepEqual(parseMarkup('`a **b** c`'), [{ kind: 'inline', code: 'a **b** c' }])
})

test('코드 블록 안의 **는 굵게로 나누지 않는다', () => {
  assert.deepEqual(parseMarkup('```py\nf(**opts)\nx = 2 ** 3 **y**\n```'), [
    { kind: 'block', lang: 'py', code: 'f(**opts)\nx = 2 ** 3 **y**' },
  ])
})

test('짝 없는 **와 띄어 쓴 **는 문자열 그대로 둔다', () => {
  assert.deepEqual(parseMarkup('a ** b'), [{ kind: 'text', text: 'a ** b' }])
  assert.deepEqual(parseMarkup('**open'), [{ kind: 'text', text: '**open' }])
  assert.deepEqual(parseMarkup('2 ** 3 ** 4'), [{ kind: 'text', text: '2 ** 3 ** 4' }])
  assert.deepEqual(parseMarkup('****'), [{ kind: 'text', text: '****' }])
})

test('줄을 넘는 **는 굵게로 나누지 않는다', () => {
  assert.deepEqual(parseMarkup('**a\nb**'), [{ kind: 'text', text: '**a\nb**' }])
})
