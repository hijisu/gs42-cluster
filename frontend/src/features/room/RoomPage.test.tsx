import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import { kstDateFromToday, kstToIso } from '../../lib/datetime'
import type { Availability, HourState, Reservation, Room } from './api'

const multi: Room = { id: 1, code: 'multipurpose', name: '다목적회의실', capacity_note: '', equipment: 'TV', status: 'open' }
const small: Room = { id: 3, code: 'universe-small', name: '유니버스룸(소)', capacity_note: '', equipment: 'TV', status: 'open' }
const rooms = [multi, small]
const rules = { open_hour: 9, close_hour: 22, step_minutes: 30, usage_rules: ['음료만 반입 가능합니다.', '사용 후 정리해 주세요.'] }
const today = kstDateFromToday(0)

function availability(states: Partial<Record<number, HourState>> = {}): Availability {
  return {
    date: today,
    rooms: rooms.map((room) => ({
      room,
      hours: Array.from({ length: 13 }, (_, i) => ({ hour: 9 + i, state: room.id === 1 ? (states[9 + i] ?? 'free') : 'free' })),
      reservations: [],
    })),
  }
}

const reservation = (over: Partial<Reservation> = {}): Reservation => ({
  id: 7,
  room: multi,
  requested_room: multi,
  start_at: kstToIso(today, '15:00'),
  end_at: kstToIso(today, '16:00'),
  purpose: '스터디',
  headcount: 4,
  note: '',
  status: 'pending',
  reject_reason: '',
  conflict: false,
  ...over,
})

const base: Handler = (req) => {
  if (req.url.endsWith('/rooms')) return { json: rooms }
  if (req.url.endsWith('/rooms/rules')) return { json: rules }
  return undefined
}

async function openPage(...handlers: Handler[]) {
  const calls = mockApi(asUser('student'), ...handlers, base)
  renderAt('/room')
  await screen.findByRole('heading', { name: '회의실 예약' })
  return calls
}

describe('회의실 예약 화면', () => {
  it('장소×시간 타임라인에 상태를 보여준다', async () => {
    await openPage((req) => (req.url.includes('/rooms/availability') ? { json: availability({ 10: 'approved', 11: 'pending' }) } : undefined))
    const row = await screen.findByRole('row', { name: '다목적회의실' })
    expect(within(row).getByText('10시 예약 확정')).toBeInTheDocument()
    expect(within(row).getByText('11시 승인 대기')).toBeInTheDocument()
    expect(within(row).getByText('12시 비어 있음')).toBeInTheDocument()
  })

  it('신청 후 타임라인에 "승인 대기"로 표시되고 내 요청에도 나타난다', async () => {
    let requested = false
    const calls = await openPage(
      (req) => (req.method === 'POST' && req.url.endsWith('/reservations') ? ((requested = true), { status: 201, json: reservation() }) : undefined),
      (req) => (req.url.includes('/rooms/availability') ? { json: availability(requested ? { 15: 'pending' } : {}) } : undefined),
    )
    await userEvent.type(screen.getByLabelText('목적'), '스터디')
    await userEvent.type(screen.getByLabelText('인원'), '4')
    await userEvent.click(screen.getByRole('button', { name: '예약 요청하기' }))

    const row = await screen.findByRole('row', { name: '다목적회의실' })
    expect(await within(row).findByText('15시 승인 대기')).toBeInTheDocument()
    const item = await screen.findByTestId('reservation-7')
    expect(within(item).getByText('승인 대기', { selector: '.pill' })).toBeInTheDocument()
    const post = calls.find((c) => c.method === 'POST' && c.url.endsWith('/reservations'))!
    expect(post.body).toEqual({ room_id: 1, start_at: kstToIso(today, '15:00'), end_at: kstToIso(today, '16:00'), purpose: '스터디', headcount: 4, note: '' })
  })

  it('필수값이 비면 요청하지 않고 안내한다', async () => {
    const calls = await openPage()
    await userEvent.click(screen.getByRole('button', { name: '예약 요청하기' }))
    expect(await screen.findByText('목적을 입력해 주세요.')).toBeInTheDocument()
    expect(screen.getByText('인원은 1~100명으로 입력해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })

  it('서버 오류 코드를 안내 문구로 바꿔 보여준다', async () => {
    await openPage((req) => (req.method === 'POST' ? { status: 400, json: { code: 'outside_hours' } } : undefined))
    await userEvent.type(screen.getByLabelText('목적'), '스터디')
    await userEvent.type(screen.getByLabelText('인원'), '4')
    await userEvent.click(screen.getByRole('button', { name: '예약 요청하기' }))
    expect(await screen.findByText(/운영 시간\(09~22시\)/)).toBeInTheDocument()
  })

  it('승인된 예약은 이용수칙 모달에서 "확인했습니다"로 확인한다', async () => {
    await openPage((req) => (req.url.endsWith('/reservations/me') ? { json: [reservation({ status: 'approved', room: small })] } : undefined))
    const item = await screen.findByTestId('reservation-7')
    expect(within(item).getByText('다목적회의실 대신 대체 배정', { exact: false })).toBeInTheDocument()
    await userEvent.click(within(item).getByRole('button', { name: '이용수칙 확인' }))
    const dialog = await screen.findByRole('dialog', { name: '회의실 이용수칙' })
    expect(await within(dialog).findByText('음료만 반입 가능합니다.')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: '확인했습니다' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(within(item).getByRole('button', { name: '이용수칙 보기' })).toBeInTheDocument()
  })

  it('반려는 사유를 보여주고, 요청 취소를 할 수 있다', async () => {
    await openPage(
      (req) => (req.url.endsWith('/reservations/me') ? { json: [reservation(), reservation({ id: 8, status: 'rejected', reject_reason: '기존 예약' })] } : undefined),
      (req) => (req.url.endsWith('/reservations/7/cancel') ? { json: reservation({ status: 'canceled' }) } : undefined),
    )
    const rejected = await screen.findByTestId('reservation-8')
    expect(within(rejected).getByText(/반려 사유: 기존 예약/)).toBeInTheDocument()
    expect(within(rejected).queryByRole('button', { name: /요청 취소/ })).toBeNull()

    await userEvent.click(within(await screen.findByTestId('reservation-7')).getByRole('button', { name: /요청 취소/ }))
    const dialog = await screen.findByRole('dialog', { name: '예약 요청을 취소할까요?' })
    await userEvent.click(within(dialog).getByRole('button', { name: '요청 취소' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(await within(screen.getByTestId('reservation-7')).findByText('취소됨', { selector: '.pill' })).toBeInTheDocument()
  })
})

describe('kstToIso', () => {
  it('KST 날짜·시각을 UTC ISO로 바꾼다', () => {
    expect(kstToIso('2026-10-20', '14:00')).toBe('2026-10-20T05:00:00.000Z')
  })
})
