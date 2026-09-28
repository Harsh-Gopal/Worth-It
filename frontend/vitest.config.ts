import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  define: {
    '__APP_VERSION__': JSON.stringify('Version 0.999'),
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
