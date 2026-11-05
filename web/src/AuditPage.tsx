import { useEffect, useState } from 'react'
import { api, ApiError, type Audit, type AuditFlags, type AuditQuestion } from './api'
import { Evidence } from './Evidence'
import { Markup } from './MarkupText'

// 감사 화면(FR-9, design.md 6.6). 표본 20문항마다 정답 키, 근거, 매핑을 보고 세 판정을 기록한다.
// 기준(requirements 7.2): 정답 키 오류 1개 이하, 인용 미지지 2개 이하, 매핑 불충실 2개 이하.
// 20문항이 다 차면 서버가 result(pass/fail)를 계산한다. 같은 문항을 다시 저장하면 다시 계산한다.

const FLAG_LABELS: [keyof AuditFlags, string][] = [
  ['answer_key_error', '정답 키 오류'],
  ['quote_unsupported', '인용이 정답을 뒷받침하지 않는다'],
  ['mapping_unfaithful', '영·한 매핑 중 충실하지 않은 구절이 있다'],
]

const NO_FLAGS: AuditFlags = { answer_key_error: false, quote_unsupported: false, mapping_unfaithful: false }

function firstOpen(a: Audit): number {
  const i = a.sample.findIndex((q) => !a.records[q])
  return i >= 0 ? i : 0
}

function AuditQuestionView({ q }: { q: AuditQuestion }) {
  return (
    <>
      <p className="key">
        {q.question_id} · {q.bucket} · {q.format}
        {q.select_count ? ` · ${q.select_count}개 선택` : ''}
      </p>
      <Markup className="stem" text={q.stem_en} />
      {q.choices && (
        <ol className="choices audit-choices">
          {q.choices.map((c) => (
            <li key={c.id} className={q.answer_key.includes(c.id) ? 'answer' : ''}>
              <strong>{c.id}.</strong> {c.text && <Markup className="choice-text" text={c.text} />}
              {c.code && (
                <pre className="code-block">
                  <code>{c.code}</code>
                </pre>
              )}
            </li>
          ))}
        </ol>
      )}
      <p className="verdict ok">
        정답 키: {q.answer_key.join(', ')}
        {q.accepted_answers && <span className="key">허용 답안: {q.accepted_answers.join(' | ')}</span>}
      </p>
      <Evidence explanation={q.explanation_ko} segments={q.segments} grounding={q.grounding} docUrl={q.doc_url} />
    </>
  )
}

type FormProps = {
  audit: Audit
  questionId: string
  onSaved: (a: Audit) => void
  onError: (e: unknown) => void
}

function RecordForm({ audit, questionId, onSaved, onError }: FormProps) {
  const saved = audit.records[questionId]
  const [flags, setFlags] = useState<AuditFlags>(saved ?? NO_FLAGS)
  const [note, setNote] = useState(saved?.note ?? '')
  const [busy, setBusy] = useState(false)

  async function save() {
    if (busy) return
    setBusy(true)
    try {
      const r = await api.recordAudit(audit.audit_id, questionId, flags, note.trim() || null)
      onSaved({ ...audit, result: r.result, records: { ...audit.records, [questionId]: r.record } })
    } catch (e) {
      onError(e)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="audit-form">
      <h3>감사 판정</h3>
      {FLAG_LABELS.map(([key, label]) => (
        <label key={key} className={flags[key] ? 'flagged' : ''}>
          <input
            type="checkbox"
            checked={flags[key]}
            onChange={(e) => setFlags({ ...flags, [key]: e.target.checked })}
          />
          {label}
        </label>
      ))}
      <textarea placeholder="메모(선택)" value={note} onChange={(e) => setNote(e.target.value)} rows={2} />
      <button onClick={save} disabled={busy}>
        {saved ? '다시 저장' : '저장'}
      </button>
      {saved && <span className="key"> 저장됨 {saved.recorded_at}</span>}
    </section>
  )
}

export default function AuditPage() {
  const [audit, setAudit] = useState<Audit | null>(null)
  const [missing, setMissing] = useState(false)
  const [index, setIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function showError(e: unknown) {
    const c = e instanceof ApiError ? e.conflict : null
    setError(c?.message ?? (c ? `처리할 수 없다: ${c.reason}` : String(e)))
  }

  function open(a: Audit) {
    setAudit(a)
    setMissing(false)
    setIndex(firstOpen(a))
  }

  useEffect(() => {
    api
      .currentAudit()
      .then(open)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) setMissing(true)
        else showError(e)
      })
  }, [])

  async function start() {
    setBusy(true)
    setError(null)
    try {
      open(await api.createAudit())
    } catch (e) {
      showError(e)
    } finally {
      setBusy(false)
    }
  }

  function onSaved(a: Audit) {
    setError(null)
    setAudit(a)
    const next = a.sample.findIndex((q, i) => i > index && !a.records[q])
    if (next >= 0) setIndex(next)
  }

  const recorded = audit ? Object.keys(audit.records).length : 0
  const q = audit?.questions[index]

  return (
    <main>
      <header>
        <h1>감사</h1>
        <span className="progress">
          {audit && (
            <>
              {audit.pool_snapshot_id} · {recorded}/{audit.sample.length}
              {audit.result && (
                <strong className={audit.result === 'pass' ? 'verdict ok' : 'verdict ng'}>
                  {' '}
                  {audit.result}
                </strong>
              )}{' '}
              ·{' '}
            </>
          )}
          <a href="#">풀이로</a>
        </span>
      </header>

      {error && <p className="error">{error}</p>}
      {missing && (
        <section>
          <p>현재 풀 스냅샷의 감사가 없다. 시작하면 표본 20문항을 뽑는다. 같은 스냅샷이면 같은 표본이다.</p>
          <button onClick={start} disabled={busy}>
            감사 시작
          </button>
        </section>
      )}

      {audit && (
        <nav className="qnav" aria-label="감사 문항 목록">
          {audit.sample.map((qid, i) => {
            const r = audit.records[qid]
            const state = !r ? '' : r.answer_key_error || r.quote_unsupported || r.mapping_unfaithful ? 'ng' : 'ok'
            return (
              <button
                key={qid}
                className={`qnav-item ${state}${i === index ? ' current' : ''}`}
                onClick={() => setIndex(i)}
                title={qid}
              >
                {i + 1}
              </button>
            )
          })}
        </nav>
      )}

      {audit && q && (
        <article className="question audit-question" data-format={q.format}>
          <AuditQuestionView q={q} />
          <RecordForm key={q.question_id} audit={audit} questionId={q.question_id} onSaved={onSaved} onError={showError} />
        </article>
      )}
    </main>
  )
}
