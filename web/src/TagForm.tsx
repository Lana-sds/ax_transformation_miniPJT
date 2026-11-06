import { useState } from 'react'
import { api, type AnswerResult, type MistakeTag } from './api'
import { createSingleFlight } from './singleFlight'
import { MarkupInline } from './MarkupText'

// 오답 태그(FR-4.1, FR-4.2). 독해 실수면 헷갈린 영어 구절을 고른다. 자동 태그는 없다(FR-4.3).
// 처음 태그하면 복습 큐가 갱신되고, 다시 저장하면 태그만 바뀐다(D-d).
type Props = {
  result: AnswerResult
  onTagged: (tag: MistakeTag, segmentId: string | null) => void
  onError: (e: unknown) => void
}

export function TagForm({ result, onTagged, onError }: Props) {
  const [tag, setTag] = useState<MistakeTag | null>(result.mistake_tag)
  const [segment, setSegment] = useState<string | null>(result.confused_segment_id)
  const [busy, setBusy] = useState(false)
  // 저장 중이면 두 번째 PUT을 보내지 않는다(ISSUE-001).
  const [flight] = useState(createSingleFlight)

  const ready = tag === 'concept' || (tag === 'reading' && !!segment)
  const unchanged =
    tag === result.mistake_tag && (tag === 'concept' || segment === result.confused_segment_id)

  async function save() {
    if (!tag || !ready || busy) return
    await flight(async () => {
      setBusy(true)
      try {
        const r = await api.tagAttempt(result.attempt_id, tag, segment)
        onTagged(r.mistake_tag, r.confused_segment_id)
      } catch (e) {
        onError(e)
      } finally {
        setBusy(false)
      }
    })
  }

  return (
    <section className="tag-form">
      <h3>오답 태그</h3>
      {!result.mistake_tag && <p className="hint">태그를 저장해야 다음 문제로 갈 수 있다.</p>}
      <div className="tag-choices">
        <label className={tag === 'reading' ? 'chosen' : ''}>
          <input
            type="radio"
            name={`tag-${result.attempt_id}`}
            checked={tag === 'reading'}
            onChange={() => setTag('reading')}
          />
          독해 실수
        </label>
        <label className={tag === 'concept' ? 'chosen' : ''}>
          <input
            type="radio"
            name={`tag-${result.attempt_id}`}
            checked={tag === 'concept'}
            onChange={() => setTag('concept')}
          />
          개념 실수
        </label>
      </div>

      {tag === 'reading' && (
        <fieldset className="segment-pick">
          <legend>헷갈린 영어 구절</legend>
          {result.segments.map((s) => (
            <label key={s.segment_id} className={segment === s.segment_id ? 'chosen' : ''}>
              <input
                type="radio"
                name={`seg-${result.attempt_id}`}
                checked={segment === s.segment_id}
                onChange={() => setSegment(s.segment_id)}
              />
              <MarkupInline className="en" text={s.en} />
              <MarkupInline className="ko" text={s.ko} />
            </label>
          ))}
        </fieldset>
      )}

      <button onClick={save} disabled={busy || !ready || unchanged}>
        {result.mistake_tag && unchanged ? '태그 저장됨' : result.mistake_tag ? '태그 바꾸기' : '태그 저장'}
      </button>
    </section>
  )
}
