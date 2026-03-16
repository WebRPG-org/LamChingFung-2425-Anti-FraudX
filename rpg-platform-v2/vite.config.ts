import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: '.',
  index: 'index.html',
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL ?? 'http://backend:8000',
        changeOrigin: true
      },
      '/ws': {
        target: process.env.VITE_WS_URL ?? 'ws://backend:8000',
        ws: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
});
