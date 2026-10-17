import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import { kstDateFromToday, kstToIso } from '../../lib/datetime'
import type { Availability, Room } from '../room/api'
import type { BlockResult, RoomBlock } from './api'

const multi: Room = { id: 1, code: 'multipurpose', name: '다목적회의실', capacity_note: '', equipment: '', status: 'open' }
const big: Room = { id: 2, code: 'universe-large', name: '유니버스룸(대)', capacity_note: '', equipment: '', status: 'open' }
const rules = { open_hour: 9, close_hour: 22, step_minutes: 30, usage_rules: ['TV 끄기'] }
const hours = Array.from({ length: 13 }, (_, i) => ({ hour: 9 + i, state: 'free' as const }))
const availability: Availability = { date: kstDateFromToday(0), rooms: [{ room: multi, hours, reservations: [] }] }

const day1 = kstDateFromToday(7)
const day2 = kstDateFromToday(14)
const block = (over: Partial<RoomBlock> = {}): RoomBlock => ({
  id: 5,
  room_id: 2,
  start_at: kstToIso(day1, '10:00'),
  end_at: kstToIso(day1, '12:00'),
  reason: '수학 교육',
  repeat: 'weekly',
  weekdays: [5],
  until: kstDateFromToday(60),
  occurrences: [
    { date: day1, start_at: kstToIso(day1, '10:00'), end_at: kstToIso(day1, '12:00') },
    { date: day2, start_at: kstToIso(day2, '10:00'), end_at: kstToIso(day2, '12:00') },
  ],
  ...over,
})
const result = (saved: boolean, conflicting: BlockResult['conflicting_reservations'] = []): BlockResult => ({ block: block(), saved, conflicting_reservations: conflicting })

const base: Handler = (req) => {
  if (req.url.endsWith('/rooms') && req.method === 'GET') return { json: [multi, big] }
  if (req.url.endsWith('/rooms/rules') && req.method === 'GET') return { json: rules }
  if (req.url.includes('/rooms/availability')) return { json: availability }
  if (req.url.includes('/staff/reservations?')) return { json: [] }
  return undefined
}
const blocks = (list: RoomBlock[]): Handler => (req) => (req.method === 'GET' && req.url.includes('/staff/room-blocks?') ? { json: list } : undefined)

async function openPage(...handlers: Handler[]) {
  const calls = mockApi(asUser('staff'), ...handlers, base)
  renderAt('/staff/room')
  await screen.findByRole('heading', { name: '회의실 관리' })
  return calls
}

describe('예약 차단 기간', () => {
  it('차단 일정을 반복 요약·남은 회차와 함께 보여준다', async () => {
    await openPage(blocks([block()]))
    const item = await screen.findByTestId('block-5')
    expect(within(item).getByText('수학 교육')).toBeInTheDocument()
    expect(within(item).getByText('유니버스룸(대)')).toBeInTheDocument()
    expect(within(item).getByText(/매주 토/)).toBeInTheDocument()
    expect(within(item).getByText(/남은 2회/)).toBeInTheDocument()
  })

  it('매주 반복 차단을 추가한다: 먼저 확인(check_only)하고 겹침이 없으면 바로 저장한다', async () => {
    const calls = await openPage(
      blocks([]),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/room-blocks') ? { status: (req.body as { check_only: boolean }).check_only ? 200 : 201, json: result(!(req.body as { check_only: boolean }).check_only) } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '차단 추가' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.selectOptions(within(dialog).getByLabelText('장소'), '유니버스룸(대)')
    await userEvent.clear(within(dialog).getByLabelText('날짜'))
    await userEvent.type(within(dialog).getByLabelText('날짜'), day1)
    await userEvent.selectOptions(within(dialog).getByLabelText('반복'), 'weekly')
    await userEvent.click(within(dialog).getByRole('button', { name: '토' }))
    await userEvent.type(within(dialog).getByLabelText('반복 종료일'), kstDateFromToday(60))
    await userEvent.type(within(dialog).getByLabelText('사유'), '수학 교육')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))

    await waitFor(() => expect(calls.filter((c) => c.method === 'POST').length).toBe(2))
    const posts = calls.filter((c) => c.method === 'POST')
    expect(posts.map((c) => (c.body as { check_only: boolean }).check_only)).toEqual([true, false])
    expect(posts[1].body).toEqual({
      room_id: 2,
      start_at: kstToIso(day1, '10:00'),
      end_at: kstToIso(day1, '12:00'),
      reason: '수학 교육',
      repeat: 'weekly',
      weekdays: [5],
      until: kstDateFromToday(60),
      check_only: false,
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  })

  it('겹치는 예약이 있으면 경고하고 확인 후에만 저장한다', async () => {
    const conflicting = [{ id: 9, room_id: 2, start_at: kstToIso(day1, '10:30'), end_at: kstToIso(day1, '11:30'), status: 'approved', purpose: '스터디' }]
    const calls = await openPage(
      blocks([]),
      (req) => (req.method === 'POST' ? { status: 200, json: result((req.body as { check_only: boolean }).check_only === false, conflicting) } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '차단 추가' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.type(within(dialog).getByLabelText('사유'), '행사')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    expect(await within(dialog).findByText(/겹치는 예약이 1건/)).toBeInTheDocument()
    expect(within(dialog).getByText(/스터디/)).toBeInTheDocument()
    expect(calls.filter((c) => c.method === 'POST')).toHaveLength(1)
    await userEvent.click(within(dialog).getByRole('button', { name: '겹치는 예약이 있어도 저장' }))
    await waitFor(() => expect(calls.filter((c) => c.method === 'POST')).toHaveLength(2))
    expect((calls.filter((c) => c.method === 'POST')[1].body as { check_only: boolean }).check_only).toBe(false)
  })

  it('필수값이 비면 요청하지 않고 안내한다(사유, 요일, 반복 종료일)', async () => {
    const calls = await openPage(blocks([]))
    await userEvent.click(await screen.findByRole('button', { name: '차단 추가' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.selectOptions(within(dialog).getByLabelText('반복'), 'weekly')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    expect(await within(dialog).findByText('차단 사유를 입력해 주세요.')).toBeInTheDocument()
    expect(within(dialog).getByText('요일을 하나 이상 골라 주세요.')).toBeInTheDocument()
    expect(within(dialog).getByText('반복 종료일을 선택해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })

  it('한 회차만 삭제하고, 전체 삭제는 확인 후 한다', async () => {
    const calls = await openPage(
      blocks([block()]),
      (req) => (req.method === 'DELETE' ? { status: 204 } : undefined),
    )
    const item = await screen.findByTestId('block-5')
    await userEvent.click(within(item).getByRole('button', { name: '수학 교육 회차 보기' }))
    await userEvent.click(within(item).getByRole('button', { name: `수학 교육 ${day2} 이 회차 삭제` }))
    await waitFor(() => expect(calls.some((c) => c.method === 'DELETE')).toBe(true))
    expect(calls.find((c) => c.method === 'DELETE')!.url).toMatch(new RegExp(`/staff/room-blocks/5/occurrences/${day2}$`))

    await userEvent.click(within(item).getByRole('button', { name: '수학 교육 전체 삭제' }))
    expect(calls.filter((c) => c.method === 'DELETE')).toHaveLength(1)
    await userEvent.click(within(item).getByRole('button', { name: '삭제 확인' }))
    await waitFor(() => expect(calls.filter((c) => c.method === 'DELETE')).toHaveLength(2))
    expect(calls.filter((c) => c.method === 'DELETE')[1].url).toMatch(/\/staff\/room-blocks\/5$/)
  })

  it('한 회차만 수정하면 회차 수정 API로 보낸다', async () => {
    const calls = await openPage(
      blocks([block()]),
      (req) => (req.method === 'PATCH' ? { json: result(!(req.body as { check_only: boolean }).check_only) } : undefined),
    )
    const item = await screen.findByTestId('block-5')
    await userEvent.click(within(item).getByRole('button', { name: '수학 교육 회차 보기' }))
    await userEvent.click(within(item).getByRole('button', { name: `수학 교육 ${day2} 이 회차 수정` }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.selectOptions(within(dialog).getByLabelText('시작'), '14:00')
    await userEvent.selectOptions(within(dialog).getByLabelText('종료'), '16:00')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    await waitFor(() => expect(calls.filter((c) => c.method === 'PATCH')).toHaveLength(2))
    const patch = calls.filter((c) => c.method === 'PATCH')[1]
    expect(patch.url).toMatch(new RegExp(`/staff/room-blocks/5/occurrences/${day2}$`))
    expect(patch.body).toMatchObject({ start_at: kstToIso(day2, '14:00'), end_at: kstToIso(day2, '16:00'), reason: '수학 교육', check_only: false })
    expect(patch.body).not.toHaveProperty('repeat')
  })

  it('현황에 차단 사유를 안내한다', async () => {
    const closedAvailability: Availability = {
      ...availability,
      rooms: [{ ...availability.rooms[0], closed: [{ start_at: kstToIso(availability.date, '10:00'), end_at: kstToIso(availability.date, '12:00'), reason: '수학 교육' }] }],
    }
    await openPage(blocks([]), (req) => (req.url.includes('/rooms/availability') ? { json: closedAvailability } : undefined))
    expect(await screen.findByText('다목적회의실 10:00–12:00 수학 교육')).toBeInTheDocument()
  })
})
