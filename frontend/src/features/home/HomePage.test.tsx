import { screen, within } from '@testing-library/react'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import { kstDateFromToday, kstToIso } from '../../lib/datetime'
import type { Meeting } from '../meeting/api'
import type { Reservation, Room } from '../room/api'
import type { Course } from '../review/api'
import type { Book, BookWish } from '../library/api'

const day = kstDateFromToday(3)
const room: Room = { id: 1, code: 'multipurpose', name: '다목적회의실', capacity_note: '', equipment: 'TV', status: 'open' }
const meeting: Meeting = {
  id: 1,
  type: { id: 1, code: 'freeze', name: '프리즈' },
  slot_at: kstToIso(day, '15:00'),
  content: '문의',
  notify_slack: true,
  status: 'confirmed',
  staff: { id: 1, name: '스태프 A' },
  location: '1층 사무실 앞',
  proposed_at: null,
}
const reservation: Reservation = {
  id: 2,
  room,
  requested_room: room,
  start_at: kstToIso(day, '15:00'),
  end_at: kstToIso(day, '18:00'),
  purpose: '스터디',
  headcount: 3,
  note: '',
  status: 'pending',
  reject_reason: '',
  conflict: false,
}
const course: Course = {
  id: 1,
  name: '경북 특화형 데이터센터 기초과정',
  start_date: '2026-09-17',
  end_date: '2026-09-26',
  location: '유니버스룸',
  intro: '',
  status: 'completed',
  review_deadline: kstDateFromToday(10),
  average_rating: 4.5,
  review_count: 2,
  participating: true,
  reviewed: false,
  can_review: true,
}

const book: Book = { id: 3, code: 'GSIA-IT-003', title: '이펙티브 타입스크립트', author: '댄 밴더캄', publisher: '인사이트', isbn: '', category: '컴퓨터/IT', quantity: 1, description: '', cover_url: '', link_url: '', pub_date: '' }
const wish: BookWish = { id: 1, title: 'Designing Data-Intensive Apps', author: '', reason: '', link_url: '', status: 'requested', staff_note: '', created_at: '2026-10-17T00:00:00Z' }

const data = (over: { meetings?: Meeting[]; reservations?: Reservation[]; courses?: Course[]; wishes?: BookWish[] } = {}): Handler => (req) => {
  if (req.url.endsWith('/books/my-requests')) return { json: { reports: [], wishes: over.wishes ?? [wish] } }
  if (req.url.includes('/books/')) return { json: { total: 1, categories: ['컴퓨터/IT'], results: [book] } }
  if (req.url.endsWith('/meetings/me')) return { json: over.meetings ?? [meeting] }
  if (req.url.endsWith('/reservations/me')) return { json: over.reservations ?? [reservation] }
  if (req.url.endsWith('/courses')) return { json: over.courses ?? [course] }
  if (req.url.endsWith('/rooms')) return { json: [room] }
  return undefined
}

async function openHome(...handlers: Handler[]) {
  mockApi(asUser('student'), ...handlers)
  renderAt('/')
  await screen.findByRole('heading', { level: 1 })
}
const card = (label: string) => screen.getByText(label, { selector: '.label' }).closest('.card') as HTMLElement

describe('교육생 홈 대시보드', () => {
  it('인사말에 intra_id를 보여준다', async () => {
    await openHome(data())
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('안녕하세요, jisu님')
  })

  it('내 현황: 다음 면담·회의실 요청·작성할 후기를 요약한다', async () => {
    await openHome(data())
    const m = card('다음 면담')
    expect(await within(m).findByText(/15:00$/)).toBeInTheDocument()
    expect(within(m).getByText('프리즈 · 1층 사무실 앞 · 스태프 A')).toBeInTheDocument()
    expect(within(m).getByText('확정', { selector: '.pill' })).toBeInTheDocument()

    const r = card('회의실 요청')
    expect(await within(r).findByText('15:00–18:00', { exact: false })).toBeInTheDocument()
    expect(within(r).getByText('다목적회의실 · 3명')).toBeInTheDocument()
    expect(within(r).getByText('승인 대기', { selector: '.pill' })).toBeInTheDocument()

    const v = card('작성할 후기')
    expect(await within(v).findByText('1건')).toBeInTheDocument()
    expect(within(v).getByText(/^마감 /)).toBeInTheDocument()
    expect(within(v).getByText('작성 대기', { selector: '.pill' })).toBeInTheDocument()
  })

  it('후기 요청 배너가 과정과 마감일을 보여주고 작성 화면으로 연결한다', async () => {
    await openHome(data())
    const banner = (await screen.findByText(/후기 요청 · 마감/)).closest('.notice') as HTMLElement
    expect(banner).toHaveTextContent('경북 특화형 데이터센터 기초과정')
    expect(within(banner).getByRole('link', { name: '후기 작성하기' })).toHaveAttribute('href', '/reviews#write')
  })

  it('데이터가 없으면 빈 상태 문구를 보여주고 배너는 없다', async () => {
    await openHome(data({ meetings: [], reservations: [], courses: [] }))
    expect(await within(card('다음 면담')).findByText('예정된 면담이 없어요.')).toBeInTheDocument()
    expect(within(card('회의실 요청')).getByText('예약 요청이 없어요.')).toBeInTheDocument()
    expect(within(card('작성할 후기')).getByText('지금 작성할 후기가 없어요.')).toBeInTheDocument()
    expect(screen.queryByText(/후기 요청 ·/)).toBeNull()
  })

  it('한 영역이 실패해도 다른 카드는 보인다', async () => {
    await openHome((req) => (req.url.endsWith('/meetings/me') ? { status: 500, json: {} } : undefined), data())
    expect(await within(card('다음 면담')).findByRole('alert')).toHaveTextContent('면담을(를) 불러오지 못했어요')
    expect(await within(card('작성할 후기')).findByText('1건')).toBeInTheDocument()
  })

  it('희망 도서 카드는 내 신청을 요약하고 도서 화면으로 연결한다', async () => {
    await openHome(data())
    const v = card('희망 도서')
    expect(await within(v).findByText('1건 신청')).toBeInTheDocument()
    expect(within(v).getByText('Designing Data-Intensive Apps')).toBeInTheDocument()
    expect(within(v).getByText('접수', { selector: '.pill' })).toBeInTheDocument()
    expect(within(v).getByRole('link', { name: /자세히 보기/ })).toHaveAttribute('href', '/library')
  })

  it('희망 도서 신청이 없으면 빈 상태를 보여준다', async () => {
    await openHome(data({ wishes: [] }))
    expect(await within(card('희망 도서')).findByText('신청한 희망 도서가 없어요.')).toBeInTheDocument()
  })

  it('바로가기: 내부 화면 링크와 외부 링크(도서·gs42stats)가 맞다', async () => {
    await openHome(data())
    const section = within(screen.getByRole('region', { name: '바로가기' }))
    expect(section.getByRole('link', { name: /면담 신청/ })).toHaveAttribute('href', '/meeting')
    expect(section.getByRole('link', { name: /회의실 예약/ })).toHaveAttribute('href', '/room')
    expect(section.getByRole('link', { name: /교육과정 후기/ })).toHaveAttribute('href', '/reviews')
    expect(section.getByRole('link', { name: /오아시스 도서/ })).toHaveAttribute('href', '/library')
    const stats = section.getByRole('link', { name: /gs42stats/ })
    expect(stats).toHaveAttribute('href', 'https://gs42stat.hijae.dev/home')
    expect(stats).toHaveAttribute('target', '_blank')
    expect(stats.getAttribute('rel')).toMatch(/noopener/)
    expect(section.getByText('문의는 #pedago')).toBeInTheDocument()
  })

  it('통합 검색창은 없다', async () => {
    await openHome(data())
    expect(screen.queryByLabelText('통합 검색')).toBeNull()
  })
})
