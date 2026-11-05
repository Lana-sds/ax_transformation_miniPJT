import { useState, type FormEvent } from 'react'
import { api, type AnswerResult, type QuizSet } from './api'
import { AnswerInput } from './formats/AnswerInput'
import { isAnswerComplete } from './formats/registry'
import { ResultPanel } from './ResultPanel'

// 형식별 입력은 formats/, 결과 화면은 ResultPanel이 맡는다.
// 오답 태그와 이어 풀기는 T4.6에서 더한다.

export default function App() {
  const [quizSet, setQuizSet] = useState<QuizSet | null>(null)
  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState<string[]>([])
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
      setAnswer([])
      setResult(null)
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!quizSet || result || busy) return
    const q = quizSet.questions[index]
    if (!isAnswerComplete(q, answer)) return
    const r = await run(() => api.submitAnswer(quizSet.set_id, q.question_id, answer))
    if (r) setResult(r)
  }

  function next() {
    setIndex(index + 1)
    setAnswer([])
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
        <article className="question" data-format={q.format}>
          <form onSubmit={submit}>
            <p className="stem">{q.stem_en}</p>
            <AnswerInput question={q} value={answer} onChange={setAnswer} disabled={!!result} />
            {!result && (
              <button type="submit" disabled={busy || !isAnswerComplete(q, answer)}>
                제출
              </button>
            )}
          </form>
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
