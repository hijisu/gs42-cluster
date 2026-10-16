import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import type { AppNotification } from './api'

const noti = (over: Partial<AppNotification> = {}): AppNotification => ({
  id: 7,
  type: 'reservation_approved',
  title: '서버 기본 제목',
  body: '다목적회의실 · 10.22 10:00–12:00',
  link: '/room',
  data: {},
  read: false,
  read_at: null,
  created_at: '2026-10-20T01:00:00Z',
  ...over,
})

const list = (items: AppNotification[]): Handler => (req) =>
  req.method === 'GET' && req.url.includes('/notifications') ? { json: { unread_count: items.filter((n) => !n.read).length, items } } : undefined

describe('앱 안 알림', () => {
  it('벨에 안 읽은 수를 보이고, 최근 안 읽은 알림을 배너로 보여준다', async () => {
    mockApi(asUser('student'), list([noti(), noti({ id: 6, type: 'meeting_confirmed', link: '/meeting', body: '10.21 15:00' })]))
    renderAt('/')
    expect(await screen.findByRole('button', { name: '알림 2개 안 읽음' })).toBeInTheDocument()
    const banner = (await screen.findByText('새 알림')).closest('.notice') as HTMLElement
    expect(within(banner).getByText('회의실 예약이 승인되었어요')).toBeInTheDocument()
  })

  it('알림이 없으면 벨만 보이고 배너는 없다', async () => {
    mockApi(asUser('student'))
    renderAt('/')
    expect(await screen.findByRole('button', { name: '알림' })).toBeInTheDocument()
    expect(screen.queryByText('새 알림')).toBeNull()
  })

  it('목록에서 알림을 누르면 읽음 처리하고 link로 이동한다', async () => {
    const calls = mockApi(
      asUser('student'),
      (req) => (req.method === 'POST' && req.url.endsWith('/notifications/6/read') ? { json: noti({ id: 6, read: true }) } : undefined),
      list([noti({ id: 6, type: 'meeting_confirmed', link: '/meeting', body: '10.21 15:00' })]),
    )
    const router = renderAt('/')
    await userEvent.click(await screen.findByRole('button', { name: '알림 1개 안 읽음' }))
    const dialog = await screen.findByRole('dialog', { name: '알림' })
    await userEvent.click(within(dialog).getByRole('button', { name: /면담이 확정되었어요/ }))
    expect(router.state.location.pathname).toBe('/meeting')
    expect(calls.some((c) => c.method === 'POST' && c.url.endsWith('/notifications/6/read'))).toBe(true)
  })

  it('모두 읽음 처리를 호출한다', async () => {
    const calls = mockApi(asUser('student'), (req) => (req.url.endsWith('/read-all') ? { json: { updated: 1 } } : undefined), list([noti()]))
    renderAt('/')
    await userEvent.click(await screen.findByRole('button', { name: '알림 1개 안 읽음' }))
    const dialog = await screen.findByRole('dialog', { name: '알림' })
    await userEvent.click(within(dialog).getByRole('button', { name: '모두 읽음 처리' }))
    expect(calls.some((c) => c.method === 'POST' && c.url.endsWith('/notifications/read-all'))).toBe(true)
  })

  it('알 수 없는 type은 서버 기본 제목으로 보여준다', async () => {
    mockApi(asUser('student'), list([noti({ type: 'something_new' as never, title: '서버 기본 제목' })]))
    renderAt('/')
    const banner = (await screen.findByText('새 알림')).closest('.notice') as HTMLElement
    expect(within(banner).getByText('서버 기본 제목')).toBeInTheDocument()
  })
})
