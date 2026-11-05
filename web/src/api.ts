// FastAPI 응답 타입과 호출(design.md 7.1).

export type Choice = { id: string; text?: string; code?: string }

export type PublicQuestion = {
  question_id: string
  bucket: string
  format: string
  select_count: number | null
  stem_en: string
  choices: Choice[] | null
}

export type QuizSet = { set_id: string; set_no: number; questions: PublicQuestion[] }

export type Segment = { segment_id: string; en: string; ko: string }

export type Grounding = { page: string; url: string; quote: string; answer_basis: string }

export type MistakeTag = 'reading' | 'concept'

export type AnswerResult = {
  attempt_id: number
  question_id: string
  answer: string[]
  correct: boolean
  answer_key: string[]
  explanation_ko: string
  segments: Segment[]
  grounding: Grounding[]
  doc_url: string | null
  mistake_tag: MistakeTag | null
  confused_segment_id: string | null
}

// GET /api/sets/{set_id}: 새로고침 뒤 이어 풀기(FR-8.1). results는 question_id로 찾는다.
export type SetDetail = QuizSet & {
  created_at: string
  completed: boolean
  results: Record<string, AnswerResult>
  untagged_attempt_ids: number[]
}

export type TagResult = {
  attempt_id: number
  question_id: string
  mistake_tag: MistakeTag
  confused_segment_id: string | null
}

// 409 본문의 detail(D-h). reason으로 경우를 나눈다.
export type ConflictDetail = {
  reason: string
  set_id?: string
  attempt_ids?: number[]
  message?: string
}

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(`${status} ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`)
    this.status = status
    this.detail = detail
  }

  // 409이고 detail이 객체면 돌려준다.
  get conflict(): ConflictDetail | null {
    if (this.status !== 409 || typeof this.detail !== 'object' || this.detail === null) return null
    return this.detail as ConflictDetail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    const text = await res.text()
    let detail: unknown = text
    try {
      const body = JSON.parse(text)
      detail = body?.detail ?? body
    } catch {
      // JSON이 아니면 원문을 둔다.
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export const api = {
  createSet: () => request<QuizSet>('/api/sets', { method: 'POST' }),
  getSet: (setId: string) => request<SetDetail>(`/api/sets/${setId}`),
  submitAnswer: (setId: string, questionId: string, answer: string[]) =>
    request<AnswerResult>(`/api/sets/${setId}/answers`, {
      method: 'POST',
      body: JSON.stringify({ question_id: questionId, answer }),
    }),
  tagAttempt: (attemptId: number, tag: MistakeTag, segmentId: string | null) =>
    request<TagResult>(`/api/attempts/${attemptId}/tag`, {
      method: 'PUT',
      body: JSON.stringify({ mistake_tag: tag, confused_segment_id: tag === 'reading' ? segmentId : null }),
    }),
}
