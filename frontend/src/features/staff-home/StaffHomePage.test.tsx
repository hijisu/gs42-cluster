import { screen, within } from '@testing-library/react'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import { kstDateFromToday } from '../../lib/datetime'
import { latestReviewRate, todaySchedule, todoItems } from './summary'
import type { StaffMeeting } from '../staff-meeting/api'
import type { StaffReservation } from '../staff-room/api'
import type { BookReport, BookWish } from '../staff-library/api'
import type { StaffCourse } from '../staff-course/api'

const today = kstDateFromToday(0)
const meeting = (over: Partial<StaffMeeting> = {}): StaffMeeting => ({
  id: 1, type: { id: 1, code: 'x', name: '프리즈' }, slot_at: `${today}T01:00:00Z`, content: '', notify_slack: false, status: 'pending',
  staff: null, location: '', proposed_at: null, student: { id: 5, intra_id: 'alice', name: '앨리스' }, staff_note: '', created_at: '2026-10-08T01:00:00Z', ...over,
})
const room = { id: 2, code: 'r', name: '다목적회의실', capacity_note: '', equipment: '', status: 'open' as const }
const reservation = (over: Partial<StaffReservation> = {}): StaffReservation => ({
  id: 3, room, requested_room: room, start_at: `${today}T06:00:00Z`, end_at: `${today}T08:00:00Z`, purpose: '프로젝트 회의', headcount: 4, note: '',
  status: 'pending', reject_reason: '', conflict: false, user: { id: 6, intra_id: 'bob', name: '밥' }, created_by_staff: false, conflict_ids: [], ...over,
})
const wish = (over: Partial<BookWish> = {}): BookWish => ({
  id: 7, title: '쿠버네티스 인 액션', author: '', reason: '', link_url: '', status: 'requested', staff_note: '', created_at: '2026-10-08T01:00:00Z',
  requester: { intra_id: 'carol', name: '캐럴' }, ...over,
})
const report = (over: Partial<BookReport> = {}): BookReport => ({
  id: 9, book_id: 1, book_code: 'B', book_title: '컴퓨터 네트워킹', kind: 'lost', detail: '', status: 'received', created_at: '2026-10-08T01:00:00Z',
  reporter: { intra_id: 'dave', name: '데이브' }, ...over,
})
const course = (over: Partial<StaffCourse> = {}): StaffCourse => ({
  id: 4, name: '데이터센터 기초과정', start_date: '2026-10-01', end_date: '2026-10-10', location: '', intro: '', status: 'completed', review_deadline: null,
  participant_count: 4, reviewed_count: 1, pending_count: 3, review_rate: 0.25, ...over,
})

describe('운영 홈 요약 계산', () => {
  it('종류별 최신순으로 최대 3건씩 묶고 처리된 도서 요청은 뺀다', () => {
    const meetings = [1, 2, 3, 4].map((i) => meeting({ id: i, created_at: `2026-10-0${i}T00:00:00Z` }))
    const items = todoItems({
      meetings, reservations: [reservation()],
      wishes: [wish(), wish({ id: 8, status: 'approved' })], reports: [report(), report({ id: 10, status: 'resolved' })],
    })
    expect(items.filter((i) => i.kind === 'meeting').map((i) => i.key)).toEqual(['m4', 'm3', 'm2'])
    expect(items.filter((i) => i.kind === 'wish')).toHaveLength(1)
    expect(items.filter((i) => i.kind === 'report')).toHaveLength(1)
    expect(items.map((i) => i.kind)).toEqual(['meeting', 'meeting', 'meeting', 'room', 'wish', 'report'])
  })

  it('오늘 일정은 오늘 확정된 면담과 승인된 예약만 시간순으로', () => {
    const items = todaySchedule(
      [meeting({ id: 1, status: 'confirmed', slot_at: `${today}T06:30:00Z`, location: '1층' }), meeting({ id: 2, status: 'confirmed', slot_at: '2020-01-01T01:00:00Z' }), meeting({ id: 3, status: 'pending' })],
      [reservation({ status: 'approved' }), reservation({ id: 4, status: 'approved', start_at: '2020-01-01T01:00:00Z' })],
      today,
    )
    expect(items.map((i) => i.key)).toEqual(['r3', 'm1'])
  })

  it('후기 작성률은 후기를 받는 가장 최근 과정 기준', () => {
    expect(latestReviewRate([course(), course({ id: 5, name: '새 과정', end_date: '2026-10-12', review_rate: 0.5 }), course({ id: 6, status: 'ongoing', end_date: '2026-12-01' })])).toEqual({ name: '새 과정', percent: 50 })
    expect(latestReviewRate([course({ review_rate: null })])).toBeNull()
  })
})

const route = (match: (url: string) => boolean, json: unknown): Handler => (req) => (req.method === 'GET' && match(req.url) ? { json } : undefined)

describe('운영 홈 화면', () => {
  it('요약 4칸과 처리 대기 요청·오늘 일정을 보여준다', async () => {
    mockApi(
      asUser('staff'),
      route((u) => u.includes('/staff/meetings?status=pending'), [meeting()]),
      route((u) => u.includes('/staff/meetings?status=confirmed'), [meeting({ id: 2, status: 'confirmed', slot_at: `${today}T06:30:00Z`, location: '1층' })]),
      route((u) => u.includes('/staff/reservations?status=pending'), [reservation({ conflict: true })]),
      route((u) => u.includes('/staff/reservations?date='), [reservation({ id: 5, status: 'approved' })]),
      route((u) => u.endsWith('/staff/book-wishes'), [wish()]),
      route((u) => u.endsWith('/staff/book-reports'), [report()]),
      route((u) => u.endsWith('/staff/courses'), [course()]),
    )
    renderAt('/staff')
    await screen.findByRole('heading', { name: '오늘 처리할 요청' })

    const stats = screen.getByRole('region', { name: '처리 대기 현황' })
    const card = (label: string) => within(stats).getByText(label).closest('.summary-card') as HTMLElement
    expect(await within(card('면담 요청')).findByText('1건')).toBeInTheDocument()
    expect(within(card('면담 요청')).getByText('담당자 배정 필요')).toBeInTheDocument()
    expect(within(card('회의실 승인 대기')).getByText('1건')).toBeInTheDocument()
    expect(within(card('도서 접수')).getByText('2건')).toBeInTheDocument()
    expect(within(stats).getByText('1건 시간 충돌')).toBeInTheDocument()
    expect(within(stats).getByText('희망 도서 1 · 분실 신고 1')).toBeInTheDocument()
    expect(within(stats).getByText('25%')).toBeInTheDocument()

    expect(await screen.findByText(/alice · 면담 · 프리즈/)).toBeInTheDocument()
    expect(screen.getByText(/bob · 회의실 · 다목적회의실/)).toBeInTheDocument()
    expect(screen.getByText(/carol · 희망 도서 · 쿠버네티스 인 액션/)).toBeInTheDocument()
    expect(screen.getByText(/dave · 분실·훼손 신고 · 컴퓨터 네트워킹/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'alice 면담 프리즈 처리' })).toHaveAttribute('href', '/staff/meeting')

    expect(await screen.findByText(/프리즈 · alice · 1층/)).toBeInTheDocument()
    expect(screen.getByText(/다목적회의실 · 프로젝트 회의/)).toBeInTheDocument()
  })

  it('요청이 없으면 안내 문구를 보여준다', async () => {
    mockApi(asUser('staff'), route((u) => u.endsWith('/staff/courses'), []))
    renderAt('/staff')
    expect(await screen.findByText('처리할 요청이 없어요.')).toBeInTheDocument()
    expect(screen.getByText('오늘 확정된 일정이 없어요.')).toBeInTheDocument()
  })

  it('조회에 실패하면 알린다', async () => {
    mockApi(asUser('staff'), (req) => (req.url.includes('/staff/book-wishes') ? { status: 500, json: {} } : undefined))
    renderAt('/staff')
    expect(await screen.findByText('일부 요청을 불러오지 못했어요.')).toBeInTheDocument()
  })
})
