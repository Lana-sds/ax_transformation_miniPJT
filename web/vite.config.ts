import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// `/api`를 FastAPI(localhost:8000)로 프록시한다. CORS 설정은 두지 않는다(design.md D-7).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
