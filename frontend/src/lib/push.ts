import { api } from './api'

// 구독 API 계약은 백엔드 #60 기준(문서화되기 전 가정): GET /push/public-key, POST·DELETE /push/subscriptions

export type PushSupport = 'ready' | 'ios-install' | 'unsupported'

const isIos = () => /iPad|iPhone|iPod/.test(navigator.userAgent)

/** 이 환경에서 푸시를 켤 수 있는지. iOS는 홈 화면에 설치한 PWA에서만 동작한다. */
export function pushSupport(): PushSupport {
  const capable = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
  if (capable) return 'ready'
  return isIos() ? 'ios-install' : 'unsupported'
}

/** base64url 공개키 → applicationServerKey */
export function urlBase64ToUint8Array(base64: string): Uint8Array<ArrayBuffer> {
  const padded = (base64 + '='.repeat((4 - (base64.length % 4)) % 4)).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(padded)
  const out = new Uint8Array(new ArrayBuffer(raw.length))
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i)
  return out
}

export const fetchPublicKey = () => api<{ public_key: string }>('/push/public-key')
export const registerSubscription = (subscription: unknown) => api<void>('/push/subscriptions', { method: 'POST', body: subscription })
export const removeSubscription = (endpoint: string) => api<void>('/push/subscriptions', { method: 'DELETE', body: { endpoint } })

/** 서비스워커 준비를 기다리되, 등록된 서비스워커가 없어 영원히 끝나지 않는 경우를 위해 시간 제한을 둔다. */
export const SW_READY_TIMEOUT_MS = 3000

export class ServiceWorkerNotReadyError extends Error {
  constructor() {
    super('service worker not ready')
  }
}

export async function serviceWorkerReady(timeoutMs = SW_READY_TIMEOUT_MS): Promise<ServiceWorkerRegistration | null> {
  const timeout = new Promise<null>((resolve) => setTimeout(() => resolve(null), timeoutMs))
  return Promise.race([navigator.serviceWorker.ready, timeout])
}

/** 현재 브라우저 구독. 서비스워커가 준비되지 않았으면 null. */
export async function currentSubscription(): Promise<PushSubscription | null> {
  const reg = await serviceWorkerReady()
  return reg ? reg.pushManager.getSubscription() : null
}

/** 권한 요청 → 브라우저 구독 → 서버 등록. 권한이 거부되면 'denied', 서비스워커가 없으면 ServiceWorkerNotReadyError. */
export async function enablePush(): Promise<'enabled' | 'denied'> {
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') return 'denied'
  const reg = await serviceWorkerReady()
  if (!reg) throw new ServiceWorkerNotReadyError()
  const { public_key } = await fetchPublicKey()
  const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(public_key) })
  await registerSubscription(sub.toJSON())
  return 'enabled'
}

/** 서버 구독을 지우고 브라우저 구독도 해제한다. */
export async function disablePush(): Promise<void> {
  const sub = await currentSubscription()
  if (!sub) return
  await removeSubscription(sub.endpoint)
  await sub.unsubscribe()
}
