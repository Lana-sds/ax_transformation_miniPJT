import { useState } from 'react'
import { api, type AnswerResult, type QuizSet } from './api'

// M0: 단일 선택만 다룬다. 다른 형식과 오답 태그, 이어 풀기는 T4.5, T4.6에서 더한다.

function ResultPanel({ result }: { result: AnswerResult }) {
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
        <p>
          <a href={result.doc_url} target="_blank" rel="noreferrer">
            코드 보기
          </a>
        </p>
      )}
    </section>
  )
}

export default function App() {
  const [quizSet, setQuizSet] = useState<QuizSet | null>(null)
  const [index, setIndex] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [result, setResult] = useState<AnswerResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(true)
    setError(null)
    try {
      return await fn()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  async function startSet() {
    const s = await run(api.createSet)
    if (s) {
      setQuizSet(s)
      setIndex(0)
      setSelected(null)
      setResult(null)
    }
  }

  async function submit() {
    if (!quizSet || !selected) return
    const q = quizSet.questions[index]
    const r = await run(() => api.submitAnswer(quizSet.set_id, q.question_id, [selected]))
    if (r) setResult(r)
  }

  function next() {
    setIndex(index + 1)
    setSelected(null)
    setResult(null)
  }

  const q = quizSet?.questions[index]
  const done = quizSet && index >= quizSet.questions.length

  return (
    <main>
      <header>
        <h1>agent-dev-quiz</h1>
        {quizSet && (
          <span className="progress">
            세트 {quizSet.set_no} · {Math.min(index + 1, quizSet.questions.length)}/{quizSet.questions.length}
          </span>
        )}
      </header>

      {error && <p className="error">{error}</p>}

      {(!quizSet || done) && (
        <button onClick={startSet} disabled={busy}>
          새 세트 시작
        </button>
      )}

      {q && !done && (
        <article className="question">
          <p className="stem">{q.stem_en}</p>
          <ul className="choices">
            {(q.choices ?? []).map((c) => (
              <li key={c.id}>
                <label className={selected === c.id ? 'chosen' : ''}>
                  <input
                    type="radio"
                    name={q.question_id}
                    value={c.id}
                    checked={selected === c.id}
                    disabled={!!result}
                    onChange={() => setSelected(c.id)}
                  />
                  <b>{c.id}.</b> {c.text}
                </label>
              </li>
            ))}
          </ul>
          {!result && (
            <button onClick={submit} disabled={busy || !selected}>
              제출
            </button>
          )}
          {result && (
            <>
              <ResultPanel result={result} />
              <button onClick={next}>다음 문제</button>
            </>
          )}
        </article>
      )}
    </main>
  )
}
