// 숫자 뒤 목적격 조사(ISSUE-003). 숫자를 한자어로 읽은 끝소리로 고른다.
// 끝자리 2·4·5·9(이, 사, 오, 구)는 받침이 없어 '를', 나머지와 0으로 끝나는 수(십, 백, 천, 만)는 '을'이다.
export function objectParticle(n: number): '을' | '를' {
  const last = Math.abs(Math.trunc(n)) % 10
  return last === 2 || last === 4 || last === 5 || last === 9 ? '를' : '을'
}
