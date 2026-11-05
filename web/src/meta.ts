import type { PublicQuestion } from './api'

// T4.8 문제 메타 라벨. topic은 정답 힌트가 될 수 있어 풀이 전에 보이지 않는다(FR-2.1).
// bucket 값은 design.md의 버킷 목록(day2~day7 순)이다. 모르는 값은 그대로 보인다.

const BUCKETS: Record<string, string> = {
  rag: 'RAG',
  langgraph_basics: 'LangGraph 기초',
  tool_mcp: '도구·MCP',
  middleware_hitl_guardrails: '미들웨어·HITL·가드레일',
  multi_agent: '멀티 에이전트',
  ops_quality: '운영·품질',
}

const FORMATS: Record<string, string> = {
  single: '단일 선택',
  multi: '복수 선택',
  short: '단답',
  code: '코드 선택',
}

const REVIEW: Record<string, string> = { wrong: '복습', seen: '다시 풀기' }

type MetaInput = Pick<PublicQuestion, 'bucket' | 'format' | 'select_count' | 'review'>

export function metaLabels(q: MetaInput): string[] {
  const format = FORMATS[q.format] ?? q.format
  const labels = [
    BUCKETS[q.bucket] ?? q.bucket,
    q.format === 'multi' && q.select_count ? `${format} ${q.select_count}개` : format,
  ]
  if (q.review) labels.push(REVIEW[q.review] ?? q.review)
  return labels
}
