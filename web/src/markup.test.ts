// 실행: web/에서 `node --test src/markup.test.ts`(Node 23.6 이상은 타입을 지우고 바로 돈다).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { parseMarkup } from './markup.ts'

test('코드 표시가 없으면 문자열 하나를 그대로 돌려준다', () => {
  assert.deepEqual(parseMarkup('Which call returns a list?'), [
    { kind: 'text', text: 'Which call returns a list?' },
  ])
})

test('빈 문자열은 빈 목록이다', () => {
  assert.deepEqual(parseMarkup(''), [])
})

test('인라인 코드를 나눈다', () => {
  assert.deepEqual(parseMarkup('Call `invoke()` on the `model` object.'), [
    { kind: 'text', text: 'Call ' },
    { kind: 'inline', code: 'invoke()' },
    { kind: 'text', text: ' on the ' },
    { kind: 'inline', code: 'model' },
    { kind: 'text', text: ' object.' },
  ])
})

test('언어 표시가 있는 코드 블록을 나누고 앞뒤 문장은 그대로 둔다', () => {
  const src = 'Given this code:\n\n```python\nx = 1\nprint(x)\n```\n\nWhat is printed?'
  assert.deepEqual(parseMarkup(src), [
    { kind: 'text', text: 'Given this code:\n\n' },
    { kind: 'block', lang: 'python', code: 'x = 1\nprint(x)' },
    { kind: 'text', text: '\n\nWhat is printed?' },
  ])
})

test('언어 표시가 없는 코드 블록', () => {
  assert.deepEqual(parseMarkup('```\na = `b`\n```'), [{ kind: 'block', lang: '', code: 'a = `b`' }])
})

test('코드 블록 안의 백틱은 인라인 코드로 나누지 않는다', () => {
  const parts = parseMarkup('See `x`:\n```js\nconst s = `t`\n```')
  assert.deepEqual(parts, [
    { kind: 'text', text: 'See ' },
    { kind: 'inline', code: 'x' },
    { kind: 'text', text: ':\n' },
    { kind: 'block', lang: 'js', code: 'const s = `t`' },
  ])
})

test('닫히지 않은 코드 블록과 짝 없는 백틱은 문자열 그대로 둔다', () => {
  assert.deepEqual(parseMarkup('```python\nx = 1'), [{ kind: 'text', text: '```python\nx = 1' }])
  assert.deepEqual(parseMarkup('a ` b'), [{ kind: 'text', text: 'a ` b' }])
})

test('CRLF 줄바꿈의 코드 블록도 나눈다', () => {
  assert.deepEqual(parseMarkup('```py\r\nx = 1\r\n```'), [{ kind: 'block', lang: 'py', code: 'x = 1' }])
})
