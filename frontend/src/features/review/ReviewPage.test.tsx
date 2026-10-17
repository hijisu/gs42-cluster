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
const other = course({ id: 2, name: '서울대학교 파이썬 AI 교육', start_date: '2026-08-18', end_date: '2026-08-27', location: '서울대', participating: false, can_review: false, average_rating: null, review_count: 0 })
const third = course({ id: 3, name: '글로벌 기업가 정신', start_date: '2026-07-19', end_date: '2026-07-28', location: '시애틀', participating: false, can_review: false, review_count: 7 })

const review = (over: Partial<Review> = {}): Review => ({
  id: 5,
  course_id: 1,
  rating: 4,
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

async function openPage(path = '/reviews', ...handlers: Handler[]) {
  const calls = mockApi(asUser('student'), ...handlers)
  renderAt(path)
  await screen.findByRole('heading', { name: /교육과정 후기|경북 특화형|서울대학교|글로벌/ })
  return calls
}

const courses = (...list: Course[]): Handler => (req) => (req.url.endsWith('/courses') ? { json: list } : undefined)
const reviewsOf = (id: number, list: Review[]): Handler => (req) => (req.url.endsWith(`/courses/${id}/reviews`) ? { json: list } : undefined)
const names = () =>
  within(screen.getByRole('table', { name: '교육과정 목록' }))
    .getAllByRole('row')
    .slice(1)
    .map((r) => within(r).getAllByRole('cell')[0].textContent?.replace('작성 가능', ''))

describe('교육과정 후기 게시판', () => {
  it('① 교육과정 목록: 과정명·교육기간·교육장소·후기 수와 후기 요청 배너(마감일)를 보여준다', async () => {
    await openPage('/reviews', courses(course(), other))
    const banner = (await screen.findByText(/후기 요청 · 마감 10\.30/)).closest('.notice') as HTMLElement
    expect(banner).toHaveTextContent('경북 특화형 데이터센터 기초과정')
    const table = await screen.findByRole('table', { name: '교육과정 목록' })
    const row = within(table).getByRole('button', { name: '경북 특화형 데이터센터 기초과정' }).closest('tr') as HTMLElement
    expect(within(row).getByText('09.17–09.26')).toBeInTheDocument()
    expect(within(row).getByText('유니버스룸')).toBeInTheDocument()
    expect(within(row).getByText('2')).toBeInTheDocument()
    expect(within(row).getByText('작성 가능')).toBeInTheDocument()
  })

  it('정렬: 등록순·과정 이름순·최신순/과거순·후기 많은 순/적은 순', async () => {
    await openPage('/reviews', courses(course(), other, third))
    await screen.findByRole('table', { name: '교육과정 목록' })
    const sortBy = (label: string) => userEvent.selectOptions(screen.getByLabelText('정렬'), label)
    expect(names()).toEqual(['경북 특화형 데이터센터 기초과정', '서울대학교 파이썬 AI 교육', '글로벌 기업가 정신'])
    await sortBy('과정 이름순')
    expect(names()).toEqual(['경북 특화형 데이터센터 기초과정', '글로벌 기업가 정신', '서울대학교 파이썬 AI 교육'])
    await sortBy('최신순')
    expect(names()).toEqual(['경북 특화형 데이터센터 기초과정', '서울대학교 파이썬 AI 교육', '글로벌 기업가 정신'])
    await sortBy('과거순')
    expect(names()).toEqual(['글로벌 기업가 정신', '서울대학교 파이썬 AI 교육', '경북 특화형 데이터센터 기초과정'])
    await sortBy('후기 많은 순')
    expect(names()).toEqual(['글로벌 기업가 정신', '경북 특화형 데이터센터 기초과정', '서울대학교 파이썬 AI 교육'])
    await sortBy('후기 적은 순')
    expect(names()).toEqual(['서울대학교 파이썬 AI 교육', '경북 특화형 데이터센터 기초과정', '글로벌 기업가 정신'])
  })

  it('② 과정명을 누르면 그 과정의 후기(제목 없음)와 돌아가기가 나온다', async () => {
    await openPage('/reviews', courses(course(), other), reviewsOf(1, [review()]))
    await userEvent.click(await screen.findByRole('button', { name: '경북 특화형 데이터센터 기초과정' }))
    expect(await screen.findByRole('heading', { name: '경북 특화형 데이터센터 기초과정' })).toBeInTheDocument()
    expect(screen.getByText(/후기 2개 · 평균 만족도 4\.5/)).toBeInTheDocument()
    expect(await screen.findByText('익명')).toBeInTheDocument()
    expect(screen.getByText('실습이 좋았어요')).toBeInTheDocument()
    expect(screen.getByText('#인프라 입문')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: '만족도 4/5' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '← 교육과정 목록' }))
    expect(await screen.findByRole('table', { name: '교육과정 목록' })).toBeInTheDocument()
  })

  it('주소(?course=)로 과정 게시판에 바로 들어간다. 후기가 없으면 안내하고 작성 불가 과정엔 작성 버튼이 없다', async () => {
    await openPage('/reviews?course=2', courses(course(), other), reviewsOf(2, []))
    expect(await screen.findByRole('heading', { name: '서울대학교 파이썬 AI 교육' })).toBeInTheDocument()
    expect(await screen.findByText(/아직 등록된 후기가 없어요/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '후기 작성' })).toBeNull()
  })

  it('후기 작성은 팝업: 제목 입력이 없고, 등록하면 닫히고 목록이 갱신된다', async () => {
    let posted = false
    const calls = await openPage(
      '/reviews?course=1',
      (req) => (req.url.endsWith('/courses') ? { json: [posted ? course({ reviewed: true, can_review: false, review_count: 3 }) : course()] } : undefined),
      (req) => (req.method === 'POST' && req.url.endsWith('/reviews') ? ((posted = true), { status: 201, json: review({ id: 9, good: '새 후기 내용', mine: true }) }) : undefined),
      (req) => (req.url.endsWith('/courses/1/reviews') ? { json: posted ? [review({ id: 9, good: '새 후기 내용', mine: true })] : [] } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '후기 작성' }))
    const dialog = await screen.findByRole('dialog', { name: '후기 작성' })
    expect(within(dialog).queryByLabelText('제목')).toBeNull()
    await userEvent.click(within(dialog).getByRole('button', { name: '4점' }))
    await userEvent.type(within(dialog).getByLabelText('좋았던 점'), '새 후기 내용')
    await userEvent.type(within(dialog).getByLabelText('태그'), '#실습 위주, 입문')
    await userEvent.click(within(dialog).getByRole('button', { name: '후기 등록' }))
    expect(await screen.findByText('새 후기 내용')).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(screen.queryByRole('button', { name: '후기 작성' })).toBeNull()
    const post = calls.find((c) => c.method === 'POST' && c.url.endsWith('/reviews'))!
    expect(post.body).toMatchObject({ course_id: 1, rating: 4, tags: ['실습 위주', '입문'], anonymous: true })
    expect(post.body).not.toHaveProperty('title')
  })

  it('?write=1로 들어오면 작성 팝업이 바로 열린다', async () => {
    await openPage('/reviews?course=1&write=1', courses(course()), reviewsOf(1, []))
    expect(await screen.findByRole('dialog', { name: '후기 작성' })).toBeInTheDocument()
  })

  it('만족도가 없으면 등록하지 않고 안내한다', async () => {
    const calls = await openPage('/reviews?course=1&write=1', courses(course()), reviewsOf(1, []))
    const dialog = await screen.findByRole('dialog', { name: '후기 작성' })
    await userEvent.click(within(dialog).getByRole('button', { name: '후기 등록' }))
    expect(await within(dialog).findByText('만족도를 선택해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })

  it('서버 오류 코드를 안내 문구로 보여준다', async () => {
    await openPage('/reviews?course=1&write=1', courses(course()), reviewsOf(1, []), (req) => (req.method === 'POST' ? { status: 409, json: { code: 'already_reviewed' } } : undefined))
    const dialog = await screen.findByRole('dialog', { name: '후기 작성' })
    await userEvent.click(within(dialog).getByRole('button', { name: '5점' }))
    await userEvent.click(within(dialog).getByRole('button', { name: '후기 등록' }))
    expect(await within(dialog).findByText('이미 후기를 작성한 과정입니다.')).toBeInTheDocument()
  })
})
