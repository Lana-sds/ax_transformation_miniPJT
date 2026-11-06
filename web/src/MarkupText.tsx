import { parseMarkup } from './markup'

// 코드 블록은 <pre><code>, 인라인 코드는 <code>, **굵게**는 <strong>으로 보이고 나머지는 문자열 그대로 둔다(T4.7).
// 근거 인용(Evidence의 blockquote)은 이 컴포넌트를 쓰지 않아 원문 그대로 보인다.
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
        if (p.kind === 'strong') return <strong key={i}>{p.text}</strong>
        return p.text
      })}
    </div>
  )
}
