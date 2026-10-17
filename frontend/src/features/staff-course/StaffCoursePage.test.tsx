import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import { kstDateFromToday } from '../../lib/datetime'
import type { StaffCourse } from './api'

const course = (over: Partial<StaffCourse> = {}): StaffCourse => ({
  id: 4,
  name: '서울대학교 파이썬 AI 교육',
  start_date: '2026-10-05',
  end_date: '2026-10-14',
  location: '유니버스룸',
  intro: '',
  status: 'completed',
  review_deadline: kstDateFromToday(14),
  participant_count: 4,
  reviewed_count: 1,
  pending_count: 3,
  review_rate: 0.25,
  ...over,
})
const upcoming = course({ id: 5, name: '경북 특화형 데이터센터 기초과정', status: 'upcoming', review_deadline: null, participant_count: 10, reviewed_count: 0, pending_count: 10, review_rate: null })
const closed = course({ id: 6, name: '지난 과정', review_deadline: '2020-01-01' })

const list = (courses: StaffCourse[]): Handler => (req) => (req.method === 'GET' && req.url.endsWith('/staff/courses') ? { json: courses } : undefined)

async function openPage(...handlers: Handler[]) {
  const calls = mockApi(asUser('staff'), ...handlers)
  renderAt('/staff/courses')
  await screen.findByRole('heading', { name: '교육과정 · 후기 관리' })
  return calls
}

describe('운영 교육과정·후기 관리 화면', () => {
  it('과정 표에 기간·참여·작성률·상태를 보여준다', async () => {
    await openPage(list([course(), upcoming, closed]))
    const table = await screen.findByRole('table', { name: '교육과정 목록' })
    const row = within(table).getByText('서울대학교 파이썬 AI 교육').closest('tr') as HTMLElement
    expect(within(row).getByText('10.05–10.14')).toBeInTheDocument()
    expect(within(row).getByText('4명')).toBeInTheDocument()
    expect(within(row).getByText('25%')).toBeInTheDocument()
    expect(within(row).getByText('후기 수집 중')).toBeInTheDocument()
    expect(within(table).getByText('모집 · 수요조사')).toBeInTheDocument()
    expect(within(table).getByText('종료', { selector: '.pill' })).toBeInTheDocument()
  })

  it('과정을 등록한다: 참여 intra ID(Enter)를 칩으로 모아 보낸다', async () => {
    const calls = await openPage(
      list([]),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/courses') ? { status: 201, json: course({ id: 9, name: '새 과정', participant_count: 2 }) } : undefined),
    )
    await userEvent.type(await screen.findByLabelText('과정명'), '새 과정')
    await userEvent.type(screen.getByLabelText('시작일'), '2026-11-18')
    await userEvent.type(screen.getByLabelText('종료일'), '2026-11-26')
    await userEvent.type(screen.getByLabelText('장소'), '유니버스룸')
    await userEvent.type(screen.getByLabelText('참여 학생'), 'Alice, bob{Enter}')
    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('bob')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '과정 등록' }))

    expect(await screen.findByText(/참여 2명 · 후기 게시판이 만들어졌어요/)).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'POST')!.body).toEqual({
      name: '새 과정',
      start_date: '2026-11-18',
      end_date: '2026-11-26',
      location: '유니버스룸',
      intro: '',
      status: 'upcoming',
      review_deadline: null,
      intra_ids: ['alice', 'bob'],
      csv: '',
    })
  })

  it('CSV 파일을 읽어 함께 보낸다', async () => {
    const calls = await openPage(list([]), (req) => (req.method === 'POST' ? { status: 201, json: course({ id: 9 }) } : undefined))
    await userEvent.type(await screen.findByLabelText('과정명'), '과정')
    await userEvent.type(screen.getByLabelText('시작일'), '2026-11-18')
    await userEvent.type(screen.getByLabelText('종료일'), '2026-11-26')
    await userEvent.upload(screen.getByLabelText('CSV 파일 선택'), new File(['intra_id\ncarol,dave'], 'students.csv', { type: 'text/csv' }))
    expect(await screen.findByText('CSV: students.csv')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '과정 등록' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'POST')).toBe(true))
    expect((calls.find((c) => c.method === 'POST')!.body as { csv: string }).csv).toBe('intra_id\ncarol,dave')
  })

  it('필수값이 비면 등록하지 않고, 서버 오류 코드를 안내한다', async () => {
    const calls = await openPage(list([]), (req) => (req.method === 'POST' ? { status: 400, json: { code: 'invalid_intra_id' } } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '과정 등록' }))
    expect(await screen.findByText('과정명을 입력해 주세요.')).toBeInTheDocument()
    expect(screen.getByText('시작일을 선택해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)

    await userEvent.type(screen.getByLabelText('과정명'), '과정')
    await userEvent.type(screen.getByLabelText('시작일'), '2026-11-18')
    await userEvent.type(screen.getByLabelText('종료일'), '2026-11-26')
    await userEvent.click(screen.getByRole('button', { name: '과정 등록' }))
    expect(await screen.findByText(/intra ID 형식이 올바르지 않아요/)).toBeInTheDocument()
  })

  it('후기 요청: 작성 완료/미작성 수를 보이고 미작성자에게만 보낸다', async () => {
    const calls = await openPage(
      list([course(), upcoming]),
      (req) => (req.url.endsWith('/review-request') ? { json: { course_id: 4, target: 'pending', recipient_count: 3, recipients: ['a', 'b', 'c'] } } : undefined),
    )
    const form = (await screen.findByRole('heading', { name: '후기 요청 보내기' })).closest('.card') as HTMLElement
    expect(within(form).getByText('1명')).toBeInTheDocument()
    expect(within(form).getByText('3명')).toBeInTheDocument()
    expect(within(form).getByLabelText('알림 문구')).toHaveValue('서울대학교 파이썬 AI 교육에 참여해 주셔서 감사합니다. 다음 교육생을 위해 후기를 남겨 주세요.')
    await userEvent.click(within(form).getByRole('button', { name: '미작성자에게 보내기' }))
    expect(await within(form).findByText('3명에게 후기 요청을 보냈어요.')).toBeInTheDocument()
    const post = calls.find((c) => c.url.endsWith('/review-request'))!
    expect(post.body).toMatchObject({ target: 'pending' })
    expect(calls.some((c) => c.method === 'PATCH')).toBe(false)
  })

  it('마감일을 바꾸면 먼저 저장한 뒤 요청을 보낸다', async () => {
    const calls = await openPage(
      list([course()]),
      (req) => (req.method === 'PATCH' ? { json: course() } : undefined),
      (req) => (req.url.endsWith('/review-request') ? { json: { course_id: 4, target: 'all', recipient_count: 4, recipients: [] } } : undefined),
    )
    const form = (await screen.findByRole('heading', { name: '후기 요청 보내기' })).closest('.card') as HTMLElement
    const deadline = within(form).getByLabelText('작성 마감')
    await userEvent.clear(deadline)
    await userEvent.type(deadline, '2099-12-31')
    await userEvent.click(within(form).getByRole('button', { name: '전체에게 보내기' }))
    expect(await within(form).findByText('4명에게 후기 요청을 보냈어요.')).toBeInTheDocument()
    const order = calls.filter((c) => c.method === 'PATCH' || c.url.endsWith('/review-request')).map((c) => c.method)
    expect(order).toEqual(['PATCH', 'POST'])
    expect(calls.find((c) => c.method === 'PATCH')!.body).toEqual({ review_deadline: '2099-12-31' })
  })

  it('후기를 받는 중인 과정이 없으면 안내한다', async () => {
    await openPage(list([upcoming]))
    expect(await screen.findByText(/후기를 받는 중인 과정이 없어요/)).toBeInTheDocument()
  })

  it("'종료 · 후기 열기'로 과정을 종료 처리한다", async () => {
    const calls = await openPage(list([upcoming]), (req) => (req.method === 'PATCH' ? { json: { ...upcoming, status: 'completed' } } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: /종료 처리·후기 열기/ }))
    await waitFor(() => expect(calls.some((c) => c.method === 'PATCH')).toBe(true))
    expect(calls.find((c) => c.method === 'PATCH')!.url).toMatch(/\/staff\/courses\/5$/)
    expect(calls.find((c) => c.method === 'PATCH')!.body).toEqual({ status: 'completed' })
  })
})
