import { useEffect, useState, type FormEvent } from 'react'
import { api, ApiError, type AnswerResult, type MistakeTag, type QuizSet } from './api'
import { AnswerInput } from './formats/AnswerInput'
import { conflictAction } from './conflict'
import { isAnswerComplete } from './formats/registry'
import { Markup } from './MarkupText'
import { metaLabels } from './meta'
import { createSingleFlight } from './singleFlight'
import { ResultPanel } from './ResultPanel'
import { TagForm } from './TagForm'

// 형식별 입력은 formats/, 결과 화면은 ResultPanel, 오답 태그는 TagForm이 맡는다.
// 진행 중인 세트 ID는 브라우저에 두고, 새로고침하면 GET /api/sets/{set_id}로 결과를 다시 받는다(FR-8.1).

const SET_KEY = 'agent-dev-quiz.set_id'

function loadSetId(): string | null {
  try {
    return localStorage.getItem(SET_KEY)
  } catch {
    return null
  }
}

function saveSetId(id: string | null) {
  try {
    if (id) localStorage.setItem(SET_KEY, id)
    else localStorage.removeItem(SET_KEY)
  } catch {
    // 저장하지 못해도 POST /api/sets의 409 untagged_wrong이 세트를 다시 알려 준다.
  }
}

type Results = Record<string, AnswerResult>

function isUntagged(r: AnswerResult | undefined): boolean {
  return !!r && !r.correct && !r.mistake_tag
}

// 볼 위치: 태그 없는 오답이 있으면 그 문제, 없으면 처음 안 푼 문제. 다 풀었으면 길이.
function resumeIndex(qs: QuizSet, results: Results): number {
  const untagged = qs.questions.findIndex((q) => isUntagged(results[q.question_id]))
  if (untagged >= 0) return untagged
  const open = qs.questions.findIndex((q) => !results[q.question_id])
  return open >= 0 ? open : qs.questions.length
}

export default function App() {
  const [quizSet, setQuizSet] = useState<QuizSet | null>(null)
  const [results, setResults] = useState<Results>({})
  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  // 처리 중이면 두 번째 요청을 보내지 않는다(ISSUE-001).
  const [flight] = useState(createSingleFlight)

  function showError(e: unknown) {
    const c = e instanceof ApiError ? e.conflict : null
    setError(c?.message ?? (c ? `처리할 수 없다: ${c.reason}` : String(e)))
  }

  async function loadSet(setId: string): Promise<boolean> {
    try {
      const d = await api.getSet(setId)
      setQuizSet({ set_id: d.set_id, set_no: d.set_no, questions: d.questions })
      setResults(d.results)
      setIndex(resumeIndex(d, d.results))
      setAnswer([])
      saveSetId(d.set_id)
      return true
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) saveSetId(null)
      else showError(e)
      return false
    }
  }

  useEffect(() => {
    const id = loadSetId()
    if (id) void loadSet(id)
  }, [])

  // 409 untagged_wrong이면 그 세트를 다시 불러 태그 입력으로 보낸다.
  // set_closed면 저장한 세트 ID를 지우고 새 세트 시작 버튼을 보인다(ISSUE-002).
  async function recover(e: unknown): Promise<boolean> {
    const c = e instanceof ApiError ? e.conflict : null
    const action = conflictAction(c, quizSet?.set_id ?? null)
    if (action.kind === 'reload') {
      if (action.notice) setNotice(action.notice)
      return loadSet(action.setId)
    }
    if (action.kind === 'closed') {
      saveSetId(null)
      setQuizSet(null)
      setResults({})
      setIndex(0)
      setAnswer([])
      setNotice(action.notice)
      return true
    }
    return false
  }

  async function run(fn: () => Promise<void>) {
    await flight(async () => {
      setBusy(true)
      setError(null)
      setNotice(null)
      try {
        await fn()
      } catch (e) {
        if (!(await recover(e))) showError(e)
      } finally {
        setBusy(false)
      }
    })
  }

  function startSet() {
    void run(async () => {
      const s = await api.createSet()
      setQuizSet(s)
      setResults({})
      setIndex(0)
      setAnswer([])
      saveSetId(s.set_id)
    })
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!quizSet || busy) return
    const q = quizSet.questions[index]
    if (results[q.question_id] || !isAnswerComplete(q, answer)) return
    void run(async () => {
      const r = await api.submitAnswer(quizSet.set_id, q.question_id, answer)
      setResults((prev) => ({ ...prev, [q.question_id]: r }))
    })
  }

  function onTagged(questionId: string, tag: MistakeTag, segmentId: string | null) {
    setResults((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], mistake_tag: tag, confused_segment_id: segmentId },
    }))
    setNotice(null)
  }

  function goTo(i: number) {
    setIndex(i)
    setAnswer([])
    setError(null)
  }

  const questions = quizSet?.questions ?? []
  const blocked = questions.some((q) => isUntagged(results[q.question_id]))
  const frontier = quizSet ? resumeIndex(quizSet, results) : 0
  const done = !!quizSet && index >= questions.length
  const q = done ? undefined : questions[index]
  const result = q ? results[q.question_id] : undefined
  const answeredCount = questions.filter((x) => results[x.question_id]).length
  const allDone = !!quizSet && answeredCount === questions.length

  return (
    <main>
      <header>
        <h1>agent-dev-quiz</h1>
        <span className="progress">
          {quizSet && (
            <>
              세트 {quizSet.set_no} · {answeredCount}/{questions.length} ·{' '}
            </>
          )}
          <a href="#audit">감사</a>
        </span>
      </header>

      {quizSet && (
        <nav className="qnav" aria-label="문제 목록">
          {questions.map((x, i) => {
            const r = results[x.question_id]
            const state = r ? (r.correct ? 'ok' : isUntagged(r) ? 'untagged' : 'ng') : 'open'
            // 푼 문제와 지금 풀 문제만 연다. 태그 없는 오답이 있으면 새 문제로 못 간다.
            const reachable = !!r || (i === frontier && !blocked)
            return (
              <button
                key={x.question_id}
                className={`qnav-item ${state}${i === index ? ' current' : ''}`}
                disabled={!reachable}
                onClick={() => goTo(i)}
                title={r ? (r.correct ? '정답' : r.mistake_tag ? `오답 · ${r.mistake_tag}` : '오답 · 태그 필요') : '안 푼 문제'}
              >
                {i + 1}
              </button>
            )
          })}
        </nav>
      )}

      {notice && <p className="notice">{notice}</p>}
      {error && <p className="error">{error}</p>}

      {(!quizSet || (allDone && !blocked)) && (
        <div className="set-actions">
          {allDone && <p>세트 {quizSet?.set_no}를 다 풀었다.</p>}
          <button onClick={startSet} disabled={busy}>
            새 세트 시작
          </button>
        </div>
      )}

      {q && (
        <article className="question" data-format={q.format}>
          <form onSubmit={submit}>
            <p className="qmeta">
              {metaLabels(q).map((label, i) => (
                <span key={i} className={i === 2 ? 'qmeta-review' : undefined}>
                  {label}
                </span>
              ))}
            </p>
            <Markup className="stem" text={q.stem_en} />
            <AnswerInput
              question={q}
              value={result ? result.answer : answer}
              onChange={setAnswer}
              disabled={!!result}
            />
            {!result && (
              <button type="submit" disabled={busy || !isAnswerComplete(q, answer)}>
                제출
              </button>
            )}
          </form>
          {result && (
            <>
              <ResultPanel result={result} />
              {!result.correct && (
                <TagForm
                  key={result.attempt_id}
                  result={result}
                  onTagged={(tag, seg) => onTagged(q.question_id, tag, seg)}
                  onError={showError}
                />
              )}
              {!allDone && (
                <button onClick={() => goTo(frontier)} disabled={blocked || frontier === index}>
                  다음 문제
                </button>
              )}
            </>
          )}
        </article>
      )}
    </main>
  )
}
