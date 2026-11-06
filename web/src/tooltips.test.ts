// IMP-1, IMP-2 머리글 툴팁 문구(06 QA 2026-11-06, docs/06-qa/output/qa-report.md).
// 실행: web/에서 `node --test src/tooltips.test.ts`.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { HEADER_TIPS } from './tooltips.ts'

test('세트 번호 툴팁 문구', () => {
  assert.equal(
    HEADER_TIPS.setNo.text,
    '지금까지 시작한 세트의 순번이다. 복습 문제가 다시 나오는 시점을 이 번호로 센다.',
  )
})

test('감사 링크 툴팁 문구', () => {
  assert.equal(
    HEADER_TIPS.audit.text,
    '고정한 문제 풀에서 무작위로 뽑은 20문항을 직접 검토하고 오류를 표시하는 화면이다.',
  )
})

test('aria-describedby로 가리킬 id는 서로 다르다', () => {
  assert.notEqual(HEADER_TIPS.setNo.id, HEADER_TIPS.audit.id)
  for (const t of Object.values(HEADER_TIPS)) assert.match(t.id, /^[a-z][a-z0-9-]*$/)
})
