import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 3000,
    proxy: {
      '/api/server': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/server/, ''),
      },
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // rewrite: (p) => p.replace(/^\/api\/client/, ''),
      },
    },
  },
});
