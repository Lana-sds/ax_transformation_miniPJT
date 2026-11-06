// 문제 문장, 보기 문장, 해설의 마크다운 코드 표시와 **굵게**만 나눈다(T4.7, ISSUE-004). 다른 마크다운은 문자열 그대로 둔다.
// JSX가 없는 순수 함수라 `node --test src/markup.test.ts`로 바로 시험한다.

export type MarkupPart =
  | { kind: 'text'; text: string }
  | { kind: 'strong'; text: string }
  | { kind: 'inline'; code: string }
  | { kind: 'block'; lang: string; code: string }

// ```lang 줄바꿈, 내용, 줄바꿈 ```. 닫는 ```가 없으면 맞지 않아 문자열로 남는다.
const FENCE = /```([^\n`]*)\r?\n([\s\S]*?)\r?\n?```/g
// 한 줄 안의 `...`. 짝이 없는 백틱은 맞지 않아 문자열로 남는다.
const INLINE = /`([^`\n]+)`/g
// 한 줄 안의 **...**. 안쪽 앞뒤가 공백이나 별표면 맞지 않는다. 짝이 없으면 문자열로 남는다.
const STRONG = /\*\*(?![\s*])([^*\n]*?[^\s*])\*\*/g

// 코드 밖 문자열에서만 굵게를 나눈다.
function splitStrong(text: string, out: MarkupPart[]) {
  let last = 0
  for (const m of text.matchAll(STRONG)) {
    if (m.index > last) out.push({ kind: 'text', text: text.slice(last, m.index) })
    out.push({ kind: 'strong', text: m[1] })
    last = m.index + m[0].length
  }
  if (last < text.length) out.push({ kind: 'text', text: text.slice(last) })
}

function splitInline(text: string, out: MarkupPart[]) {
  let last = 0
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) splitStrong(text.slice(last, m.index), out)
    out.push({ kind: 'inline', code: m[1] })
    last = m.index + m[0].length
  }
  if (last < text.length) splitStrong(text.slice(last), out)
}

export function parseMarkup(src: string): MarkupPart[] {
  const out: MarkupPart[] = []
  let last = 0
  for (const m of src.matchAll(FENCE)) {
    splitInline(src.slice(last, m.index), out)
    out.push({ kind: 'block', lang: m[1].trim(), code: m[2] })
    last = m.index + m[0].length
  }
  splitInline(src.slice(last), out)
  return out
}
