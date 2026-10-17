/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// 이 파일은 Node 에서 실행된다. @types/node 를 추가하지 않고 필요한 부분만 선언한다.
declare const process: { env: Record<string, string | undefined> }

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      // 웹 푸시 핸들러가 필요해 직접 작성한 서비스워커(src/sw.ts)를 쓴다.
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      registerType: 'autoUpdate',
      // 개발 서버(npm run dev)에서도 서비스워커를 등록해 푸시 구독을 확인할 수 있게 한다(module 서비스워커: Chrome 계열).
      devOptions: { enabled: true, type: 'module' },
      manifest: {
        name: '42gs-cluster',
        short_name: 'gs42',
        description: '42경산 교육생 요청과 교육운영팀 처리를 한곳에서',
        lang: 'ko',
        start_url: '/',
        display: 'standalone',
        background_color: '#F2F2EE',
        theme_color: '#00BABC',
        // 홈 화면 설치(Android Chrome)에는 192/512 PNG 아이콘이 필요하다.
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-maskable-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
          { src: 'icon.svg', sizes: 'any', type: 'image/svg+xml' },
        ],
      },
    }),
  ],
  server: {
    // 개발 중 /api 요청은 백엔드(Django)로 전달한다.
    // docker compose 에서는 API_PROXY_TARGET=http://backend:8000 으로 백엔드 서비스에 연결한다.
    proxy: { '/api': process.env.API_PROXY_TARGET ?? 'http://localhost:8000' },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
})
