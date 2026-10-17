import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import { kstDateFromToday, kstToIso } from '../../lib/datetime'
import type { Availability, HourState, Room } from '../room/api'
import type { StaffReservation } from './api'

const today = kstDateFromToday(0)
const multi: Room = { id: 1, code: 'multipurpose', name: '다목적회의실', capacity_note: '', equipment: 'TV', status: 'open' }
const big: Room = { id: 2, code: 'universe-large', name: '유니버스룸', capacity_note: '', equipment: '', status: 'blocked' }
const small: Room = { id: 3, code: 'universe-small', name: '유니버스룸(소)', capacity_note: '', equipment: 'TV', status: 'open' }
const rooms = [multi, big, small]
const rules = { open_hour: 9, close_hour: 22, step_minutes: 30, usage_rules: ['음료만 반입 가능합니다.', 'TV 끄기'] }

const hours = (busy: number[] = [], state: HourState = 'approved') =>
  Array.from({ length: 13 }, (_, i) => ({ hour: 9 + i, state: busy.includes(9 + i) ? state : ('free' as HourState) }))
const availability: Availability = {
  date: today,
  rooms: [
    { room: multi, hours: hours([15, 16, 17]), reservations: [] },
    { room: big, hours: hours([], 'free'), reservations: [] },
    { room: small, hours: hours(), reservations: [] },
  ],
}

const reservation = (over: Partial<StaffReservation> = {}): StaffReservation => ({
  id: 11,
  room: multi,
  requested_room: multi,
  start_at: kstToIso(today, '15:00'),
  end_at: kstToIso(today, '18:00'),
  purpose: '프로젝트 회의',
  headcount: 3,
  note: '',
  status: 'pending',
  reject_reason: '',
  conflict: true,
  user: { id: 3, intra_id: 'jisu', name: '지수' },
  created_by_staff: false,
  conflict_ids: [2],
  ...over,
})

const base: Handler = (req) => {
  if (req.url.endsWith('/rooms') && req.method === 'GET') return { json: rooms }
  if (req.url.endsWith('/rooms/rules') && req.method === 'GET') return { json: rules }
  if (req.url.includes('/rooms/availability')) return { json: availability }
  return undefined
}
const pending = (list: StaffReservation[]): Handler => (req) => (req.url.includes('/staff/reservations?') ? { json: list } : undefined)

async function openPage(...handlers: Handler[]) {
  const calls = mockApi(asUser('staff'), ...handlers, base)
  renderAt('/staff/room')
  await screen.findByRole('heading', { name: '회의실 관리' })
  return calls
}

describe('운영 회의실 관리 화면', () => {
  it('승인 대기 카드에 충돌 경고와 비어 있는 대체 장소만 보여준다', async () => {
    await openPage(pending([reservation(), reservation({ id: 12, purpose: '스터디', conflict: false, conflict_ids: [], start_at: kstToIso(today, '19:00'), end_at: kstToIso(today, '21:00') })]))
    const conflict = await screen.findByTestId('pending-11')
    expect(within(conflict).getByText('시간 충돌')).toBeInTheDocument()
    expect(within(conflict).getByText(/같은 시간에 비어 있는 장소: 유니버스룸\(소\)/)).toBeInTheDocument()
    const options = within(within(conflict).getByLabelText('대체 장소')).getAllByRole('option')
    expect(options.map((o) => o.textContent)).toEqual(['유니버스룸(소)'])
    expect(within(await screen.findByTestId('pending-12')).getByText('예약 가능')).toBeInTheDocument()
  })

  it('승인 대기는 날짜와 무관하게 전체를 시작 시각 순으로 보여준다', async () => {
    const later = kstDateFromToday(3)
    const calls = await openPage(
      pending([
        reservation({ id: 21, purpose: '나중', conflict: false, conflict_ids: [], start_at: kstToIso(later, '10:00'), end_at: kstToIso(later, '11:00') }),
        reservation({ id: 22, purpose: '먼저', conflict: false, conflict_ids: [], start_at: kstToIso(today, '10:00'), end_at: kstToIso(today, '11:00') }),
      ]),
    )
    const cards = await screen.findAllByTestId(/^pending-/)
    expect(cards.map((c) => c.dataset.testid)).toEqual(['pending-22', 'pending-21'])
    const list = calls.find((c) => c.url.includes('/staff/reservations?'))!
    expect(list.url).not.toContain('date=')
    expect(list.url).toContain('status=pending')
  })

  it('승인하면 요청이 사라진다', async () => {
    let approved = false
    const calls = await openPage(
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/reservations/11/approve') ? ((approved = true), { json: reservation({ status: 'approved' }) }) : undefined),
      (req) => (req.url.includes('/staff/reservations?') ? { json: approved ? [] : [reservation()] } : undefined),
    )
    await userEvent.click(within(await screen.findByTestId('pending-11')).getByRole('button', { name: '승인 · 이용수칙 전송' }))
    await waitFor(() => expect(screen.queryByTestId('pending-11')).toBeNull())
    expect(screen.getByText('이 날짜에 승인 대기 중인 요청이 없어요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST' && c.url.endsWith('/approve'))).toBe(true)
  })

  it('이미 승인된 예약과 겹치면(409) 안내하고 대기 상태를 유지한다', async () => {
    await openPage(pending([reservation()]), (req) => (req.method === 'POST' ? { status: 409, json: { code: 'room_conflict' } } : undefined))
    const card = await screen.findByTestId('pending-11')
    await userEvent.click(within(card).getByRole('button', { name: '승인 · 이용수칙 전송' }))
    expect(await within(card).findByRole('alert')).toHaveTextContent('이미 승인된 예약이 있어요')
    expect(screen.getByTestId('pending-11')).toBeInTheDocument()
  })

  it('대체 장소로 승인한다', async () => {
    const calls = await openPage(pending([reservation()]), (req) => (req.url.endsWith('/reassign') ? { json: reservation({ status: 'approved', room: small }) } : undefined))
    await userEvent.click(within(await screen.findByTestId('pending-11')).getByRole('button', { name: '대체 장소로 승인' }))
    await waitFor(() => expect(calls.some((c) => c.url.endsWith('/staff/reservations/11/reassign'))).toBe(true))
    expect(calls.find((c) => c.url.endsWith('/reassign'))!.body).toEqual({ room_id: 3 })
  })

  it('반려는 사유가 필수이고 사유를 보낸다', async () => {
    const calls = await openPage(pending([reservation()]), (req) => (req.url.endsWith('/reject') ? { json: reservation({ status: 'rejected' }) } : undefined))
    await userEvent.click(within(await screen.findByTestId('pending-11')).getByRole('button', { name: '반려' }))
    const dialog = await screen.findByRole('dialog', { name: '예약 요청 반려' })
    await userEvent.click(within(dialog).getByRole('button', { name: '반려' }))
    expect(await within(dialog).findByText('반려 사유를 입력해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.url.endsWith('/reject'))).toBe(false)
    await userEvent.type(within(dialog).getByLabelText('반려 사유'), '해당 시간 기존 예약')
    await userEvent.click(within(dialog).getByRole('button', { name: '반려' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(calls.find((c) => c.url.endsWith('/reject'))!.body).toEqual({ reason: '해당 시간 기존 예약' })
  })

  it('운영팀 직접 예약은 바로 승인된 예약으로 만든다', async () => {
    const calls = await openPage(pending([]), (req) => (req.method === 'POST' && req.url.endsWith('/staff/reservations') ? { status: 201, json: reservation({ status: 'approved', created_by_staff: true }) } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '운영팀 직접 예약' }))
    const dialog = await screen.findByRole('dialog', { name: '운영팀 직접 예약' })
    await userEvent.type(within(dialog).getByLabelText('목적'), '교육 준비')
    await userEvent.type(within(dialog).getByLabelText('인원'), '5')
    await userEvent.click(within(dialog).getByRole('button', { name: '바로 예약' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(calls.find((c) => c.method === 'POST' && c.url.endsWith('/staff/reservations'))!.body).toEqual({
      room_id: 1,
      start_at: kstToIso(today, '10:00'),
      end_at: kstToIso(today, '11:00'),
      purpose: '교육 준비',
      headcount: 5,
      note: '',
    })
  })

  it('이용수칙과 운영 시간을 편집해 저장한다', async () => {
    const calls = await openPage(pending([]), (req) => (req.method === 'PUT' && req.url.endsWith('/staff/rooms/rules') ? { json: rules } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '편집' }))
    const dialog = await screen.findByRole('dialog', { name: '이용수칙 편집' })
    const area = within(dialog).getByLabelText('이용수칙')
    await userEvent.clear(area)
    await userEvent.type(area, '쓰레기 치우기')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(calls.find((c) => c.method === 'PUT')!.body).toEqual({ open_hour: 9, close_hour: 22, usage_rules: ['쓰레기 치우기'] })
  })

  it('장소를 차단/해제하고 장소를 추가한다', async () => {
    const calls = await openPage(
      pending([]),
      (req) => (req.method === 'PATCH' ? { json: { ...multi, status: 'blocked' } } : undefined),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/rooms') ? { status: 201, json: { ...small, id: 9, name: '새 회의실' } } : undefined),
    )
    expect(await screen.findByText('교육 기간 차단')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '다목적회의실 차단' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'PATCH')).toBe(true))
    expect(calls.find((c) => c.method === 'PATCH')!.url).toMatch(/\/staff\/rooms\/1$/)
    expect(calls.find((c) => c.method === 'PATCH')!.body).toEqual({ status: 'blocked' })

    await userEvent.click(screen.getByRole('button', { name: '장소 추가' }))
    const dialog = await screen.findByRole('dialog', { name: '장소 추가' })
    await userEvent.type(within(dialog).getByLabelText('이름'), '새 회의실')
    await userEvent.click(within(dialog).getByRole('button', { name: '추가' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(calls.find((c) => c.method === 'POST' && c.url.endsWith('/staff/rooms'))!.body).toEqual({ name: '새 회의실', capacity_note: '', equipment: '' })
  })
})
