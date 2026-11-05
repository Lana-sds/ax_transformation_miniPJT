// 실행: web/에서 `node --test src/meta.test.ts`(Node 23.6 이상은 타입을 지우고 바로 돈다).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { metaLabels } from './meta.ts'

const base = { question_id: 'q', stem_en: 's', choices: null, select_count: null, review: null }

test('bucket과 형식을 한글 라벨로 바꾼다', () => {
  assert.deepEqual(metaLabels({ ...base, bucket: 'middleware_hitl_guardrails', format: 'single' }), [
    '미들웨어·HITL·가드레일',
    '단일 선택',
  ])
  assert.deepEqual(metaLabels({ ...base, bucket: 'rag', format: 'short' }), ['RAG', '단답'])
  assert.deepEqual(metaLabels({ ...base, bucket: 'tool_mcp', format: 'code' }), ['도구·MCP', '코드 선택'])
})

test('복수 선택은 고를 개수를 붙인다', () => {
  assert.deepEqual(metaLabels({ ...base, bucket: 'multi_agent', format: 'multi', select_count: 2 }), [
    '멀티 에이전트',
    '복수 선택 2개',
  ])
})

test('복습 여부를 붙인다', () => {
  assert.deepEqual(metaLabels({ ...base, bucket: 'ops_quality', format: 'single', review: 'wrong' }), [
    '운영·품질',
    '단일 선택',
    '복습',
  ])
  assert.deepEqual(metaLabels({ ...base, bucket: 'langgraph_basics', format: 'single', review: 'seen' }), [
    'LangGraph 기초',
    '단일 선택',
    '다시 풀기',
  ])
})

test('모르는 값은 그대로 보인다', () => {
  assert.deepEqual(metaLabels({ ...base, bucket: 'new_bucket', format: 'essay' }), ['new_bucket', 'essay'])
})
