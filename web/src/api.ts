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
  mistake_tag: string | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`${res.status} ${detail}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  createSet: () => request<QuizSet>('/api/sets', { method: 'POST' }),
  submitAnswer: (setId: string, questionId: string, answer: string[]) =>
    request<AnswerResult>(`/api/sets/${setId}/answers`, {
      method: 'POST',
      body: JSON.stringify({ question_id: questionId, answer }),
    }),
}
