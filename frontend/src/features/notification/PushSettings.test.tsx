import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { urlBase64ToUint8Array } from '../../lib/push'
import { mockApi } from '../../test-utils'
import { PushSettings } from './PushSettings'

function stubPush(opts: { permission?: 'granted' | 'denied'; existing?: boolean } = {}) {
  const unsubscribe = vi.fn(async () => true)
  const subscription = { endpoint: 'https://push.example/abc', toJSON: () => ({ endpoint: 'https://push.example/abc', keys: { p256dh: 'p', auth: 'a' } }), unsubscribe }
  const subscribe = vi.fn(async () => subscription)
  const pushManager = { getSubscription: vi.fn(async () => (opts.existing ? subscription : null)), subscribe }
  Object.defineProperty(navigator, 'serviceWorker', { value: { ready: Promise.resolve({ pushManager }) }, configurable: true })
  vi.stubGlobal('PushManager', class {})
  vi.stubGlobal('Notification', { requestPermission: vi.fn(async () => opts.permission ?? 'granted') })
  return { subscribe, unsubscribe, pushManager }
}

afterEach(() => {
  Reflect.deleteProperty(navigator, 'serviceWorker')
  vi.unstubAllGlobals()
})

describe('푸시 알림 설정', () => {
  it('푸시를 지원하지 않는 브라우저에서는 앱 안 알림만 안내한다', () => {
    render(<PushSettings />)
    expect(screen.getByText(/푸시 알림을 지원하지 않아요/)).toBeInTheDocument()
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('iOS에서 설치 전이면 홈 화면 설치를 안내한다', () => {
    vi.spyOn(navigator, 'userAgent', 'get').mockReturnValue('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)')
    render(<PushSettings />)
    expect(screen.getByText(/홈 화면에 추가/)).toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('켜면 권한 요청 → 구독 → 서버 등록을 한다', async () => {
    const { subscribe } = stubPush()
    const calls = mockApi((req) => (req.url.endsWith('/push/public-key') ? { json: { public_key: 'AQAB' } } : undefined), (req) => (req.method === 'POST' ? { status: 201, json: {} } : undefined))
    render(<PushSettings />)
    await userEvent.click(await screen.findByRole('button', { name: '푸시 알림 켜기' }))
    expect(await screen.findByRole('button', { name: '푸시 알림 끄기' })).toBeInTheDocument()
    expect(subscribe).toHaveBeenCalledWith({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array('AQAB') })
    const post = calls.find((c) => c.method === 'POST')!
    expect(post.url).toMatch(/\/push\/subscriptions$/)
    expect(post.body).toEqual({ endpoint: 'https://push.example/abc', keys: { p256dh: 'p', auth: 'a' } })
  })

  it('권한을 거부하면 안내하고 구독하지 않는다', async () => {
    const { subscribe } = stubPush({ permission: 'denied' })
    const calls = mockApi()
    render(<PushSettings />)
    await userEvent.click(await screen.findByRole('button', { name: '푸시 알림 켜기' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('차단돼 있어요')
    expect(subscribe).not.toHaveBeenCalled()
    expect(calls).toHaveLength(0)
  })

  it('이미 구독 중이면 "끄기"가 서버 구독을 지우고 브라우저 구독을 해제한다', async () => {
    const { unsubscribe } = stubPush({ existing: true })
    const calls = mockApi((req) => (req.method === 'DELETE' ? { status: 204 } : undefined))
    render(<PushSettings />)
    await userEvent.click(await screen.findByRole('button', { name: '푸시 알림 끄기' }))
    expect(await screen.findByRole('button', { name: '푸시 알림 켜기' })).toBeInTheDocument()
    await waitFor(() => expect(unsubscribe).toHaveBeenCalled())
    expect(calls.find((c) => c.method === 'DELETE')!.body).toEqual({ endpoint: 'https://push.example/abc' })
  })

  it('서버에 푸시가 설정되지 않았으면(503) 전용 안내를 보여준다', async () => {
    stubPush()
    mockApi((req) => (req.url.endsWith('/push/public-key') ? { status: 503, json: { code: 'push_not_configured' } } : undefined))
    render(<PushSettings />)
    await userEvent.click(await screen.findByRole('button', { name: '푸시 알림 켜기' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('아직 설정되지 않았어요')
  })

  it('알 수 없는 서버 오류는 일반 오류로 안내한다', async () => {
    stubPush()
    mockApi((req) => (req.url.endsWith('/push/public-key') ? { status: 500, json: {} } : undefined))
    render(<PushSettings />)
    await userEvent.click(await screen.findByRole('button', { name: '푸시 알림 켜기' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('바꾸지 못했어요')
  })

  describe('서비스워커가 등록되지 않은 환경(개발 서버 등)', () => {
    function stubNoServiceWorker() {
      // ready가 영원히 끝나지 않는 상태를 흉내 낸다.
      Object.defineProperty(navigator, 'serviceWorker', { value: { ready: new Promise(() => {}) }, configurable: true })
      vi.stubGlobal('PushManager', class {})
      vi.stubGlobal('Notification', { requestPermission: vi.fn(async () => 'granted') })
    }
    afterEach(() => vi.useRealTimers())

    it('버튼을 영구 비활성으로 두지 않고 안내 문구를 보여준다', async () => {
      vi.useFakeTimers()
      stubNoServiceWorker()
      render(<PushSettings />)
      expect(screen.getByRole('button', { name: '푸시 알림 켜기' })).toBeDisabled() // 확인 중
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3100)
      })
      expect(screen.getByRole('button', { name: '푸시 알림 켜기' })).toBeEnabled()
      expect(screen.getByRole('alert')).toHaveTextContent('서비스워커가 아직 준비되지 않았어요')
    })

    it('눌러도 구독하지 않고 같은 안내를 보여준다', async () => {
      vi.useFakeTimers()
      stubNoServiceWorker()
      const calls = mockApi()
      render(<PushSettings />)
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3100)
      })
      await act(async () => {
        screen.getByRole('button', { name: '푸시 알림 켜기' }).click()
        await vi.advanceTimersByTimeAsync(3100)
      })
      expect(screen.getByRole('alert')).toHaveTextContent('서비스워커가 아직 준비되지 않았어요')
      expect(calls.filter((c) => c.method === 'POST')).toHaveLength(0)
    })
  })
})
