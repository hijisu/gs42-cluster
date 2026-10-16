/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: '42gs-cluster',
        short_name: 'gs42',
        description: '42경산 교육생 요청과 교육운영팀 처리를 한곳에서',
        lang: 'ko',
        start_url: '/',
        display: 'standalone',
        background_color: '#F2F2EE',
        theme_color: '#00BABC',
        icons: [
          { src: 'icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' },
        ],
      },
    }),
  ],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
})
