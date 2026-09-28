import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { execSync } from 'child_process'

// Retrieve git commit count for versioning
let commitCount = 'unknown'
try {
  commitCount = execSync('git rev-list --count HEAD').toString().trim()
} catch (e) {
  console.warn('Could not retrieve git commit count')
}
const appVersion = `Version 0.${commitCount}`

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  define: {
    '__APP_VERSION__': JSON.stringify(appVersion),
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
