import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// VanishDrop frontend build config.
// Output goes to ./dist; the FastAPI backend mounts that directory at /.
// dev server proxies /api → http://127.0.0.1:8000 so `npm run dev`
// works against a locally-running backend without CORS.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/d': 'http://127.0.0.1:8000',
      '/healthz': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
