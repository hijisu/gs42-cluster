import userEvent from '@testing-library/user-event'
import { screen, within } from '@testing-library/react'
import { anonymous, asUser, mockApi, renderAt } from '../test-utils'
import { staffNav, studentNav } from './routes'
import type { Role } from '../features/auth/api'

const paths = [...studentNav, ...staffNav].map((n) => n.path)

function mockMe(role: Role | null) {
  mockApi(role ? asUser(role) : anonymous)
}

afterEach(() => vi.unstubAllGlobals())

describe('routes', () => {
  it('라우트가 10개이고 시안 파일 이름과 1:1이다', () => {
    expect(paths).toHaveLength(10)
    expect(new Set([...studentNav, ...staffNav].map((n) => n.design)).size).toBe(10)
  })

  it.each(paths)('운영팀 계정은 %s 가 열린다', async (path) => {
    mockMe('staff')
    renderAt(path)
    expect(await screen.findByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
  })

})

describe('인증 가드', () => {
  it('미로그인이면 보호 라우트에서 /login 으로 보낸다', async () => {
    mockMe(null)
    const router = renderAt('/meeting')
    expect(await screen.findByRole('heading', { name: '로그인' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/login')
  })

  it('교육생이 운영 라우트에 가면 교육생 홈으로 돌려보낸다', async () => {
    mockMe('student')
    const router = renderAt('/staff/meeting')
    await screen.findByRole('main')
    expect(router.state.location.pathname).toBe('/')
  })

  it('로그인하면 사이드바에 intra_id가 보이고, 교육생에게는 화면 전환 토글이 없다', async () => {
    mockMe('student')
    renderAt('/')
    expect(await screen.findByText('jisu')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '교육운영팀 화면 보기' })).toBeNull()
  })

  it('운영팀 계정에는 "교육운영팀 화면 보기" 토글이 있다', async () => {
    mockMe('staff')
    renderAt('/')
    expect(await screen.findByRole('link', { name: '교육운영팀 화면 보기' })).toBeInTheDocument()
  })

  it('로그인된 운영팀 계정은 로그인 화면에서 운영 홈으로 간다', async () => {
    mockMe('staff')
    const router = renderAt('/login')
    await screen.findByRole('main')
    expect(router.state.location.pathname).toBe('/staff')
  })

  it('로그인된 교육생 계정은 로그인 화면에서 교육생 홈으로 간다', async () => {
    mockMe('student')
    const router = renderAt('/login')
    await screen.findByRole('main')
    expect(router.state.location.pathname).toBe('/')
  })

  it('미로그인으로 /를 열었다가 운영팀으로 로그인하면 운영 홈으로 간다', async () => {
    let loggedIn = false
    mockApi(
      (req) => (req.url.endsWith('/auth/mock-login') ? ((loggedIn = true), { json: { intra_id: 'staff', role: 'staff' } }) : undefined),
      (req) => (req.url.endsWith('/auth/me') ? (loggedIn ? asUser('staff')(req) : anonymous(req)) : undefined),
    )
    const router = renderAt('/')
    await screen.findByRole('heading', { name: '로그인' })
    await userEvent.click(screen.getByRole('button', { name: '운영팀' }))
    await screen.findByRole('main')
    expect(router.state.location.pathname).toBe('/staff')
  })

  it('로그인 화면은 콜백 오류 코드를 문구로 보여준다', async () => {
    mockMe(null)
    renderAt('/login?error=invalid_state')
    expect(await screen.findByRole('alert')).toHaveTextContent('만료')
    expect(screen.getByRole('link', { name: '42 intra로 로그인' })).toHaveAttribute('href', '/api/auth/login')
  })
})

describe('접근성: 레이아웃', () => {
  it('본문 바로가기 링크가 main으로 연결된다', async () => {
    mockMe('student')
    renderAt('/')
    const skip = await screen.findByRole('link', { name: '본문 바로가기' })
    expect(skip).toHaveAttribute('href', '#main')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main')
  })

  it('현재 메뉴에 aria-current가 표시된다', async () => {
    mockMe('student')
    renderAt('/meeting')
    const nav = await screen.findByRole('navigation', { name: '주요 메뉴' })
    const current = within(nav).getByRole('link', { current: 'page' })
    expect(current).toHaveTextContent('면담 신청')
  })
})

describe('도서 메뉴', () => {
  it('메뉴의 도서 항목은 내부 도서 화면으로 연결된다', async () => {
    mockMe('student')
    renderAt('/')
    const nav = await screen.findByRole('navigation', { name: '주요 메뉴' })
    const link = within(nav).getByRole('link', { name: /오아시스 도서/ })
    expect(link).toHaveAttribute('href', '/library')
    expect(link).not.toHaveAttribute('target')
  })

  it('/library 에서 도서 화면이 열린다', async () => {
    mockMe('student')
    renderAt('/library')
    expect(await screen.findByRole('heading', { level: 1, name: '오아시스 도서' })).toBeInTheDocument()
    expect(screen.getByRole('search')).toBeInTheDocument()
  })
})
