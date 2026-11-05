import { useEffect, useState } from 'react'
import App from './App.tsx'
import AuditPage from './AuditPage.tsx'

// 라우터 없이 해시로 나눈다. `#audit`이면 감사 화면(T5.3), 그 밖에는 풀이 화면이다.
export default function Root() {
  const [hash, setHash] = useState(window.location.hash)
  useEffect(() => {
    const onChange = () => setHash(window.location.hash)
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return hash === '#audit' ? <AuditPage /> : <App />
}
