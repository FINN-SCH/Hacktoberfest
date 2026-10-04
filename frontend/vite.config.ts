import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react(), {
    name: 'serve-vad-runtime-modules',
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        // ONNX loads these copied modules at runtime. Vite's ?import marker
        // must not route them through transforms that reject public files.
        if (req.url && /^\/vad\/ort-wasm[\w.-]*\.mjs(?:\?|$)/.test(req.url)) {
          req.url = req.url.split('?')[0];
        }
        next();
      });
    },
  }],
  server: { proxy: { '/api': 'http://localhost:5050' } },
  test: { environment: 'node' },
});
