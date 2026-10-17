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

/** 서비스워커가 준비되지 않아 푸시를 쓸 수 없을 때(미등록·설치 실패 등). */
export class ServiceWorkerNotReady extends Error {
  constructor() {
    super('service worker not ready')
  }
}

/**
 * 서비스워커 등록이 준비되면 돌려준다. `navigator.serviceWorker.ready`는 서비스워커가 하나도 등록되지 않으면
 * 영원히 끝나지 않으므로(예: 개발 서버, 설치 실패) 제한 시간 안에 오지 않으면 ServiceWorkerNotReady 로 실패시킨다.
 */
export function readyRegistration(timeoutMs = 3000): Promise<ServiceWorkerRegistration> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new ServiceWorkerNotReady()), timeoutMs)
    navigator.serviceWorker.ready.then(
      (reg) => {
        clearTimeout(timer)
        resolve(reg)
      },
      (err) => {
        clearTimeout(timer)
        reject(err)
      },
    )
  })
}

export async function currentSubscription(): Promise<PushSubscription | null> {
  const reg = await readyRegistration()
  return reg.pushManager.getSubscription()
}

/** 권한 요청 → 브라우저 구독 → 서버 등록. 권한이 거부되면 'denied'. */
export async function enablePush(): Promise<'enabled' | 'denied'> {
  // 권한 팝업을 띄우기 전에 서비스워커부터 확인한다(준비 안 됐는데 권한만 묻지 않도록).
  const reg = await readyRegistration()
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') return 'denied'
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
