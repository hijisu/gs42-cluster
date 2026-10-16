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

  it('임시 홈에 면담/회의실 바로가기가 있다', async () => {
    mockMe('student')
    renderAt('/')
    const main = within(await screen.findByRole('main'))
    expect(main.getByRole('link', { name: '면담 신청' })).toHaveAttribute('href', '/meeting')
    expect(main.getByRole('link', { name: '회의실 예약' })).toHaveAttribute('href', '/room')
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

  it('로그인 화면은 콜백 오류 코드를 문구로 보여준다', async () => {
    mockMe(null)
    renderAt('/login?error=invalid_state')
    expect(await screen.findByRole('alert')).toHaveTextContent('만료')
    expect(screen.getByRole('link', { name: '42 intra로 로그인' })).toHaveAttribute('href', '/api/auth/login')
  })
})
