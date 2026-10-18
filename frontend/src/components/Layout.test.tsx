import { fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { anonymous, asUser, mockApi, renderAt } from '../test-utils'

function stubViewport(mobile: boolean) {
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: mobile && query.includes('max-width'),
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }))
}

afterEach(() => vi.unstubAllGlobals())

describe('레이아웃: 데스크톱', () => {
  it('사이드바에 메뉴가 있고 메뉴 열기 버튼은 없다', async () => {
    stubViewport(false)
    mockApi(asUser('student'))
    renderAt('/')
    expect(await screen.findByRole('navigation', { name: '주요 메뉴' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '메뉴 열기' })).toBeNull()
  })
})

describe('레이아웃: 모바일(≤900px)', () => {
  it('상단 바만 보이고 메뉴는 열기 전에는 DOM에 없다', async () => {
    stubViewport(true)
    mockApi(asUser('student'))
    renderAt('/')
    expect(await screen.findByRole('button', { name: '메뉴 열기' })).toBeInTheDocument()
    expect(screen.queryByRole('navigation', { name: '주요 메뉴' })).toBeNull()
    expect(screen.getByRole('button', { name: '알림' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'jisu 계정' })).toBeInTheDocument()
  })

  it('메뉴 버튼으로 드로어를 열고, 항목을 누르면 이동하며 닫힌다', async () => {
    stubViewport(true)
    mockApi(asUser('student'))
    const router = renderAt('/')
    await userEvent.click(await screen.findByRole('button', { name: '메뉴 열기' }))
    const drawer = await screen.findByRole('dialog', { name: '메뉴' })
    const nav = within(drawer).getByRole('navigation', { name: '주요 메뉴' })
    await userEvent.click(within(nav).getByRole('link', { name: /회의실 예약/ }))
    expect(router.state.location.pathname).toBe('/room')
    expect(screen.queryByRole('dialog', { name: '메뉴' })).toBeNull()
  })

  it('Esc로 드로어를 닫고 메뉴 버튼으로 포커스가 돌아온다', async () => {
    stubViewport(true)
    mockApi(asUser('student'))
    renderAt('/')
    const opener = await screen.findByRole('button', { name: '메뉴 열기' })
    await userEvent.click(opener)
    await screen.findByRole('dialog', { name: '메뉴' })
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog', { name: '메뉴' })).toBeNull()
    expect(opener).toHaveFocus()
  })

  it('운영팀 계정 드로어에는 화면 전환 없이 로그아웃만 있다', async () => {
    stubViewport(true)
    mockApi(asUser('staff'))
    renderAt('/staff')
    await userEvent.click(await screen.findByRole('button', { name: '메뉴 열기' }))
    const drawer = await screen.findByRole('dialog', { name: '메뉴' })
    expect(within(drawer).queryByRole('link', { name: '교육생 화면 보기' })).toBeNull()
    expect(within(drawer).getByRole('button', { name: '로그아웃' })).toBeInTheDocument()
    expect(screen.getByText('STAFF')).toBeInTheDocument()
  })

  it('교육생 드로어에는 화면 전환 링크가 없다', async () => {
    stubViewport(true)
    mockApi(asUser('student'))
    renderAt('/')
    await userEvent.click(await screen.findByRole('button', { name: '메뉴 열기' }))
    const drawer = await screen.findByRole('dialog', { name: '메뉴' })
    expect(within(drawer).queryByRole('link', { name: '교육운영팀 화면 보기' })).toBeNull()
    expect(within(drawer).getByRole('button', { name: '로그아웃' })).toBeInTheDocument()
  })

  it('로그인 전에는 레이아웃 없이 로그인 화면으로 간다', async () => {
    stubViewport(true)
    mockApi(anonymous)
    renderAt('/meeting')
    expect(await screen.findByRole('heading', { name: '로그인' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '메뉴 열기' })).toBeNull()
  })
})


it('프로필 사진을 표시하고 실패하면 이니셜로 돌아간다', async () => {
  stubViewport(false)
  mockApi(req => req.url.endsWith('/auth/me') ? { json: { id: 1, intra_id: 'jisu', name: '지수', role: 'student', slack_id: null, image_url: 'https://cdn.example/photo.jpg' } } : undefined)
  renderAt('/')
  const photo = await screen.findByRole('img', { name: 'jisu 프로필 사진' })
  expect(photo).toHaveAttribute('src', 'https://cdn.example/photo.jpg')
  fireEvent.error(photo)
  expect(screen.queryByRole('img', { name: 'jisu 프로필 사진' })).toBeNull()
  expect(screen.getByText('JI')).toBeInTheDocument()
})
