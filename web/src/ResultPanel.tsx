import type { AnswerResult } from './api'

// 답 제출 뒤 결과 화면(FR-2.2~FR-2.4). 오답 태그(T4.6)는 이 패널 아래에 붙인다.
// doc_url은 코드형에만 있다(pipeline/nodes.py). 있으면 "코드 보기"를 공식 문서 페이지로 건다.
export function ResultPanel({ result }: { result: AnswerResult }) {
  return (
    <section className="result">
      <p className={result.correct ? 'verdict ok' : 'verdict ng'}>
        {result.correct ? '정답' : '오답'}
        <span className="key">
          정답: {result.answer_key.join(', ')} · 내 답: {result.answer.join(', ')}
        </span>
      </p>

      <h3>해설</h3>
      <p className="explanation">{result.explanation_ko}</p>

      <h3>영·한 구절 매핑</h3>
      <table className="segments">
        <tbody>
          {result.segments.map((s) => (
            <tr key={s.segment_id}>
              <td className="en">{s.en}</td>
              <td className="ko">{s.ko}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>근거</h3>
      {result.grounding.map((g, i) => (
        <div className="grounding" key={i}>
          <a href={g.url} target="_blank" rel="noreferrer">
            {g.page}
          </a>
          <blockquote>{g.quote}</blockquote>
          <p className="basis">{g.answer_basis}</p>
        </div>
      ))}
      {result.doc_url && (
        <p className="doc-link">
          <a href={result.doc_url} target="_blank" rel="noreferrer">
            코드 보기
          </a>
        </p>
      )}
    </section>
  )
}
