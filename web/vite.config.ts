import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// `/api`를 FastAPI(localhost:8000)로 프록시한다. CORS 설정은 두지 않는다(design.md D-7).
// API 문서 화면 `/docs`(Swagger UI), `/scalar`(Scalar), `/redoc`(ReDoc)과 세 화면이 읽는 `/openapi.json`도 같은 서버로 넘긴다(개발 편의).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/docs': 'http://localhost:8000',
      '/scalar': 'http://localhost:8000',
      '/redoc': 'http://localhost:8000',
      '/openapi.json': 'http://localhost:8000',
    },
  },
})
