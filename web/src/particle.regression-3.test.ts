// Regression test for ISSUE-003 (세트 완료 문장의 조사가 틀린다), 06 QA 2026-11-06, docs/06-qa/output/qa-report.md
// 실행: web/에서 `node --test src/particle.regression-3.test.ts`.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { objectParticle } from './particle.ts'

test('끝자리가 이, 사, 오, 구로 읽히면 를이다', () => {
  for (const n of [2, 4, 5, 9, 12]) assert.equal(objectParticle(n), '를', String(n))
})

test('끝자리가 일, 삼, 육, 칠, 팔이거나 십, 백으로 끝나면 을이다', () => {
  for (const n of [1, 3, 6, 7, 8, 10, 20, 100]) assert.equal(objectParticle(n), '을', String(n))
})
