import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],

  // Base path must match Django's STATIC_URL for dev server compatibility
  base: '/static/',

  build: {
    manifest: 'manifest.json',
    outDir: resolve(__dirname, '../static/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/main.ts'),
      },
      output: {
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'css/[name]-[hash][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        },
      },
    },
  },

  server: {
    host: 'localhost',
    port: 5173,
    strictPort: true,
    cors: {
      origin: ['http://localhost:8000', 'http://127.0.0.1:8000'],
    },
  },

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@islands': resolve(__dirname, 'src/islands'),
    },
  },

  optimizeDeps: {
    include: ['react', 'react-dom', 'alpinejs', 'htmx.org'],
  },
});
