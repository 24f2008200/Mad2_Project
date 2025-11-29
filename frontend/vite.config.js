import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: "0.0.0.0",          // bind to all interfaces
    port: 5173,
    strictPort: false,        // auto-pick a port if 5173 is busy
    allowedHosts: "all",      // accept all hostnames
    hmr: {
      host: "localhost",      // fixes HMR over WSL/Windows
    },
    open: false,              // optional: do not auto-open browser
  },
  preview: {
    host: "0.0.0.0",          // same as dev server, for preview builds
    port: 4173,
  }
})
