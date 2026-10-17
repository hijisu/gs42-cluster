// 서비스워커: 정적 파일 프리캐시 + 웹 푸시 표시/클릭 이동. (vite-plugin-pwa injectManifest)
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'
import { parsePushPayload, safeLink } from './lib/pushPayload'

// DOM lib과 충돌하지 않도록 서비스워커 전역에서 쓰는 부분만 좁게 선언한다.
interface WorkerEvent extends Event {
  waitUntil(p: Promise<unknown>): void
}
interface PushEventLike extends WorkerEvent {
  data: { text(): string } | null
}
interface ClickEventLike extends WorkerEvent {
  notification: { close(): void; data?: { link?: string } }
}
interface WindowClientLike {
  url: string
  focus(): Promise<unknown>
  navigate?(url: string): Promise<unknown>
}
interface WorkerScope {
  __WB_MANIFEST: { url: string; revision: string | null }[]
  registration: { showNotification(title: string, options: { body: string; icon: string; data: { link: string } }): Promise<void> }
  clients: { matchAll(o: { type: 'window'; includeUncontrolled: boolean }): Promise<WindowClientLike[]>; openWindow(url: string): Promise<unknown> }
  skipWaiting(): void
  addEventListener(type: string, listener: (e: never) => void): void
}
const sw = self as unknown as WorkerScope

cleanupOutdatedCaches()
// 프리캐시 목록은 빌드 때 workbox가 이 식에 주입한다(별칭을 쓰면 찾지 못함). 개발 서버에서는 주입되지 않아 undefined이므로 빈 목록으로 대체한다.
precacheAndRoute((self as unknown as WorkerScope).__WB_MANIFEST ?? [])

sw.addEventListener('install', () => sw.skipWaiting())

sw.addEventListener('push', (event: PushEventLike) => {
  const msg = parsePushPayload(event.data?.text())
  event.waitUntil(sw.registration.showNotification(msg.title, { body: msg.body, icon: '/icon.svg', data: { link: msg.link } }))
})

sw.addEventListener('notificationclick', (event: ClickEventLike) => {
  event.notification.close()
  const link = safeLink(event.notification.data?.link ?? '/')
  event.waitUntil(
    sw.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async (windows) => {
      const open = windows[0]
      if (open) {
        await open.focus()
        if (open.navigate) await open.navigate(link)
        return
      }
      await sw.clients.openWindow(link)
    }),
  )
})
