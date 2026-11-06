import type { Grounding, Segment } from './api'
import { Markup, MarkupInline } from './MarkupText'

// 해설, 영·한 구절 매핑, 근거, 코드 보기 링크. 풀이 결과(ResultPanel)와 감사 화면(AuditPage)이 같이 쓴다.
// doc_url은 코드형에만 있다(pipeline/nodes.py). 있으면 "코드 보기"를 공식 문서 페이지로 건다.
type Props = {
  explanation: string
  segments: Segment[]
  grounding: Grounding[]
  docUrl: string | null
}

export function Evidence({ explanation, segments, grounding, docUrl }: Props) {
  return (
    <>
      <h3>해설</h3>
      <Markup className="explanation" text={explanation} />

      <h3>영·한 구절 매핑</h3>
      <table className="segments">
        <tbody>
          {segments.map((s) => (
            <tr key={s.segment_id}>
              <td className="en">
                <MarkupInline text={s.en} />
              </td>
              <td className="ko">
                <MarkupInline text={s.ko} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>근거</h3>
      {grounding.map((g, i) => (
        <div className="grounding" key={i}>
          <a href={g.url} target="_blank" rel="noreferrer">
            {g.page}
          </a>
          <blockquote>{g.quote}</blockquote>
          <p className="basis">{g.answer_basis}</p>
        </div>
      ))}
      {docUrl && (
        <p className="doc-link">
          <a href={docUrl} target="_blank" rel="noreferrer">
            코드 보기
          </a>
        </p>
      )}
    </>
  )
}
