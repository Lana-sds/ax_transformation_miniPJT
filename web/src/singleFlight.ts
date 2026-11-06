// 한 번에 하나만 도는 비동기 호출(ISSUE-001). disabled={busy}는 다시 그리기 전 두 번째 클릭을 못 막는다.
// 잠금은 동기로 걸리고, 처리 중에 다시 부르면 아무것도 하지 않고 false를 돌려준다.
export function createSingleFlight() {
  let pending = false
  return async function run(fn: () => Promise<void>): Promise<boolean> {
    if (pending) return false
    pending = true
    try {
      await fn()
      return true
    } finally {
      pending = false
    }
  }
}
