import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // 프로젝트 루트의 .env 파일을 참조 (VITE_* 환경변수 통합 관리)
  envDir: '../',
})