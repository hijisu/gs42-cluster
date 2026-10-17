import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import type { Course, Review } from './api'

const course = (over: Partial<Course> = {}): Course => ({
  id: 1,
  name: '경북 특화형 데이터센터 기초과정',
  start_date: '2026-09-17',
  end_date: '2026-09-26',
  location: '유니버스룸',
  intro: '',
  status: 'completed',
  review_deadline: '2026-10-30',
  average_rating: 4.5,
  review_count: 2,
  participating: true,
  reviewed: false,
  can_review: true,
  ...over,
})
const other = course({ id: 2, name: '서울대학교 파이썬 AI 교육', participating: false, can_review: false, average_rating: null, review_count: 0 })

const review = (over: Partial<Review> = {}): Review => ({
  id: 5,
  course_id: 1,
  rating: 4,
  title: '물리 인프라부터 한 번에',
  good: '실습이 좋았어요',
  bad: '',
  recommend_to: '',
  tags: ['인프라 입문'],
  anonymous: true,
  author: null,
  mine: false,
  created_at: '2026-10-01T00:00:00Z',
  ...over,
})

async function openPage(...handlers: Handler[]) {
  const calls = mockApi(asUser('student'), ...handlers)
  renderAt('/reviews')
  await screen.findByRole('heading', { name: '교육과정 후기' })
  return calls
}

describe('교육과정 후기 화면', () => {
  it('후기 요청 배너(마감일), 과정 필터, 후기 카드(익명)를 보여준다', async () => {
    await openPage(
      (req) => (req.url.endsWith('/courses') ? { json: [course(), other] } : undefined),
      (req) => (req.url.endsWith('/courses/1/reviews') ? { json: [review()] } : undefined),
    )
    const banner = (await screen.findByText(/후기 요청 · 마감 10\.30/)).closest('.notice') as HTMLElement
    expect(banner).toHaveTextContent('경북 특화형 데이터센터 기초과정')
    expect(await screen.findByRole('heading', { name: '물리 인프라부터 한 번에' })).toBeInTheDocument()
    expect(screen.getByText('익명')).toBeInTheDocument()
    expect(screen.getByText('#인프라 입문')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: '만족도 4/5' })).toBeInTheDocument()
  })

  it('과정 chip을 고르면 평균 만족도·후기 수를 보여준다', async () => {
    await openPage((req) => (req.url.endsWith('/courses') ? { json: [course(), other] } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '경북 특화형 데이터센터 기초과정' }))
    expect(await screen.findByText('4.5')).toBeInTheDocument()
    expect(screen.getByText('평균 만족도')).toBeInTheDocument()
  })

  it('"내가 참여한 과정"에 작성 상태를 보여준다 (참여하지 않은 과정은 제외)', async () => {
    await openPage((req) => (req.url.endsWith('/courses') ? { json: [course(), other] } : undefined))
    const card = (await screen.findByRole('heading', { name: '내가 참여한 과정' })).closest('.card') as HTMLElement
    expect(within(card).getByText('작성 대기')).toBeInTheDocument()
    expect(within(card).queryByText('서울대학교 파이썬 AI 교육')).toBeNull()
  })

  it('작성하면 목록과 상태가 "작성 완료"로 바뀐다', async () => {
    let posted = false
    const calls = await openPage(
      (req) => (req.url.endsWith('/courses') ? { json: [posted ? course({ reviewed: true, can_review: false, review_count: 3 }) : course()] } : undefined),
      (req) => (req.method === 'POST' && req.url.endsWith('/reviews') ? ((posted = true), { status: 201, json: review({ id: 9, title: '새 후기', mine: true }) }) : undefined),
      (req) => (req.url.endsWith('/courses/1/reviews') ? { json: posted ? [review({ id: 9, title: '새 후기', mine: true })] : [] } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '4점' }))
    await userEvent.type(screen.getByLabelText('제목'), '새 후기')
    await userEvent.type(screen.getByLabelText('태그'), '#실습 위주, 입문')
    await userEvent.click(screen.getByRole('button', { name: '후기 등록' }))

    expect(await screen.findByRole('heading', { name: '새 후기' })).toBeInTheDocument()
    const card = screen.getByRole('heading', { name: '내가 참여한 과정' }).closest('.card') as HTMLElement
    expect(await within(card).findByText('작성 완료')).toBeInTheDocument()
    expect(screen.getByText(/지금 후기를 작성할 수 있는 과정이 없어요/)).toBeInTheDocument()
    const post = calls.find((c) => c.method === 'POST' && c.url.endsWith('/reviews'))!
    expect(post.body).toMatchObject({ course_id: 1, rating: 4, title: '새 후기', tags: ['실습 위주', '입문'], anonymous: true })
  })

  it('만족도·제목이 없으면 등록하지 않고 안내한다', async () => {
    const calls = await openPage((req) => (req.url.endsWith('/courses') ? { json: [course()] } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '후기 등록' }))
    expect(await screen.findByText('만족도를 선택해 주세요.')).toBeInTheDocument()
    expect(screen.getByText('제목을 입력해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })

  it('서버 오류 코드를 안내 문구로 보여준다', async () => {
    await openPage(
      (req) => (req.url.endsWith('/courses') ? { json: [course()] } : undefined),
      (req) => (req.method === 'POST' ? { status: 409, json: { code: 'already_reviewed' } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '5점' }))
    await userEvent.type(screen.getByLabelText('제목'), '제목')
    await userEvent.click(screen.getByRole('button', { name: '후기 등록' }))
    expect(await screen.findByText('이미 후기를 작성한 과정입니다.')).toBeInTheDocument()
  })
})
