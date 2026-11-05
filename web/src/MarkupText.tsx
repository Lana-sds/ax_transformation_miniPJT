import { parseMarkup } from './markup'

// 코드 블록은 <pre><code>, 인라인 코드는 <code>로 보이고 나머지는 문자열 그대로 둔다(T4.7).
// <pre>가 들어갈 수 있어 감싸는 요소는 <p>가 아니라 <div>다.
export function Markup({ text, className }: { text: string; className?: string }) {
  return (
    <div className={className ? `markup ${className}` : 'markup'}>
      {parseMarkup(text).map((p, i) => {
        if (p.kind === 'block')
          return (
            <pre className="code-block" key={i}>
              <code data-lang={p.lang || undefined}>{p.code}</code>
            </pre>
          )
        if (p.kind === 'inline')
          return (
            <code className="inline-code" key={i}>
              {p.code}
            </code>
          )
        return p.text
      })}
    </div>
  )
}
