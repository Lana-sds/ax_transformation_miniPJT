import type { AnswerResult } from './api'
import { Evidence } from './Evidence'

// 답 제출 뒤 결과 화면(FR-2.2~FR-2.4). 오답 태그(T4.6)는 이 패널 아래에 붙인다.
// 해설, 매핑, 근거, 코드 보기 링크는 Evidence가 그린다.
export function ResultPanel({ result }: { result: AnswerResult }) {
  return (
    <section className="result">
      <p className={result.correct ? 'verdict ok' : 'verdict ng'}>
        {result.correct ? '정답' : '오답'}
        <span className="key">
          정답: {result.answer_key.join(', ')} · 내 답: {result.answer.join(', ')}
        </span>
      </p>
      <Evidence
        explanation={result.explanation_ko}
        segments={result.segments}
        grounding={result.grounding}
        docUrl={result.doc_url}
      />
    </section>
  )
}
