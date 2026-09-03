import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend runs on port 8000 by default. Proxy /api to it during dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
