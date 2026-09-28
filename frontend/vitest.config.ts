import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  define: {
    // Match the same define as vite.config.ts so tests don't get ReferenceError
    '__APP_VERSION__': JSON.stringify('Version 999'),
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
