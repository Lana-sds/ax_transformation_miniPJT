// Regression test for ISSUE-001 (새 세트 시작 두 번 누르면 POST /api/sets가 두 번 간다), 06 QA 2026-11-06, docs/06-qa/output/qa-report.md
// 실행: web/에서 `node --test src/singleFlight.regression-1.test.ts`.
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createSingleFlight } from './singleFlight.ts'

function deferred() {
  let resolve!: () => void
  let reject!: (e: unknown) => void
  const promise = new Promise<void>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

test('처리 중에 같은 줄로 다시 부르면 아무것도 하지 않는다', async () => {
  const flight = createSingleFlight()
  const d = deferred()
  let calls = 0
  const fn = () => {
    calls += 1
    return d.promise
  }
  const first = flight(fn)
  const second = flight(fn)
  assert.equal(calls, 1)
  assert.equal(await second, false)
  d.resolve()
  assert.equal(await first, true)
})

test('끝나면 다시 부를 수 있다', async () => {
  const flight = createSingleFlight()
  let calls = 0
  await flight(async () => {
    calls += 1
  })
  await flight(async () => {
    calls += 1
  })
  assert.equal(calls, 2)
})

test('실패해도 잠금을 풀고 오류는 그대로 넘긴다', async () => {
  const flight = createSingleFlight()
  await assert.rejects(
    flight(async () => {
      throw new Error('boom')
    }),
    /boom/,
  )
  let ran = false
  await flight(async () => {
    ran = true
  })
  assert.equal(ran, true)
})
