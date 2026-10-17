import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import type { Meeting } from './api'

const types = [
  { id: 1, code: 'freeze', name: '프리즈' },
  { id: 2, code: 'dormitory', name: '기숙사 이용' },
]
// 오늘을 수요일(2026-10-14 KST)로 고정: 이번 주 목요일(10-15) 15:00 가능·16:00 마감·17:00 불가, 다음 주 월요일(10-19) 15:00 가능
const TODAY = '2026-10-14'
const day = '2026-10-15'
const nextMonday = '2026-10-19'
const slots = [
  { start_at: `${day}T06:00:00Z`, state: 'open', available: true, remaining: 1 },
  { start_at: `${day}T07:00:00Z`, state: 'full', available: false, remaining: 0 },
  { start_at: `${day}T08:00:00Z`, state: 'unavailable', available: false, remaining: 0 },
  { start_at: `${nextMonday}T06:00:00Z`, state: 'open', available: true, remaining: 2 },
]
const created: Meeting = {
  id: 7,
  type: types[0],
  slot_at: slots[0].start_at,
  content: '문의',
  notify_slack: true,
  status: 'pending',
  staff: null,
  location: '',
  proposed_at: null,
}

const base: Handler = (req) => {
  if (req.url.includes('/meetings/types')) return { json: types }
  if (req.url.includes('/meetings/slots')) return { json: slots }
  return undefined
}

async function openPage(...extra: Handler[]) {
  const calls = mockApi(asUser('student'), ...extra, base)
  renderAt('/meeting')
  await screen.findByRole('heading', { name: '면담 신청' })
  return calls
}

describe('면담 신청 화면', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(`${TODAY}T03:00:00Z`))
  })
  afterEach(() => vi.useRealTimers())

  it('유형 chip, 가능/마감 격자, 이용 안내 문구를 보여준다', async () => {
    await openPage()
    expect(await screen.findByRole('button', { name: '프리즈' })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /15:00 가능/ })).toBeInTheDocument()
    expect(screen.getByLabelText(/16:00 마감/)).toBeInTheDocument()
    expect(screen.getByLabelText("10.15 17:00 불가")).toBeInTheDocument()
    expect(screen.getByText('#pedago 이용 안내')).toBeInTheDocument()
  })

  it('월~금 5열을 한 번에 보여주고 주 단위로 이동한다', async () => {
    await openPage()
    const grid = await screen.findByRole('group', { name: '희망 시간 선택' })
    expect(within(grid).getAllByText(/^(월|화|수|목|금)$/)).toHaveLength(5)
    expect(within(grid).queryByText('토')).toBeNull()
    expect(screen.getByText('10.12 ~ 10.16')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '이전 주' })).toBeDisabled()
    expect(within(grid).queryByRole('button', { name: /10\.19 15:00 가능/ })).toBeNull()
    await userEvent.click(screen.getByRole('button', { name: '다음 주' }))
    expect(screen.getByText('10.19 ~ 10.23')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /10\.19 15:00 가능/ })).toBeInTheDocument()
    // 데이터가 없는 칸은 불가로 표시한다
    expect(screen.getByLabelText('10.20 15:00 불가')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '이전 주' }))
    expect(screen.getByText('10.12 ~ 10.16')).toBeInTheDocument()
  })

  it('신청하면 내역에 "배정 중"으로 즉시 반영된다', async () => {
    const calls = await openPage((req) => (req.method === 'POST' && req.url.endsWith('/meetings') ? { status: 201, json: created } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '프리즈' }))
    await userEvent.click(await screen.findByRole('button', { name: /15:00 가능/ }))
    await userEvent.type(screen.getByLabelText('문의 내용'), '문의')
    await userEvent.click(screen.getByRole('button', { name: '면담 신청하기' }))

    const table = await screen.findByRole('table', { name: '내 면담 신청 내역' })
    expect(await within(table).findByText('배정 중', { selector: '.pill' })).toBeInTheDocument()
    const post = calls.find((c) => c.method === 'POST' && c.url.endsWith('/meetings'))!
    expect(post.body).toEqual({ type_id: 1, slot_at: slots[0].start_at, content: '문의', notify_slack: true })
  })

  it('필수 항목이 비어 있으면 신청하지 않고 안내한다', async () => {
    const calls = await openPage()
    await userEvent.click(await screen.findByRole('button', { name: '면담 신청하기' }))
    expect(await screen.findByText('문의 내용을 입력해 주세요.')).toBeInTheDocument()
    expect(screen.getByText(/면담 유형을 선택해 주세요/)).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })

  it('마감(409 slot_unavailable)이면 안내 문구를 보여준다', async () => {
    await openPage((req) => (req.method === 'POST' ? { status: 409, json: { code: 'slot_unavailable' } } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '프리즈' }))
    await userEvent.click(await screen.findByRole('button', { name: /15:00 가능/ }))
    await userEvent.type(screen.getByLabelText('문의 내용'), '문의')
    await userEvent.click(screen.getByRole('button', { name: '면담 신청하기' }))
    expect(await screen.findByText('방금 마감된 시간입니다. 다른 시간을 선택해 주세요.')).toBeInTheDocument()
  })

  it('내역에서 취소하면 상태가 "취소됨"으로 바뀐다', async () => {
    await openPage(
      (req) => (req.url.endsWith('/meetings/me') ? { json: [created] } : undefined),
      (req) => (req.url.endsWith('/meetings/7/cancel') ? { json: { ...created, status: 'canceled' } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: /프리즈 취소/ }))
    const dialog = await screen.findByRole('dialog', { name: '면담을 취소할까요?' })
    await userEvent.click(within(dialog).getByRole('button', { name: '면담 취소' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(await screen.findByText('취소됨', { selector: '.pill' })).toBeInTheDocument()
  })

  it('확정된 면담에는 취소 버튼이 없고 안내가 있다. 조율 중에는 취소할 수 있다', async () => {
    await openPage((req) => (req.url.endsWith('/meetings/me') ? { json: [{ ...created, id: 8, status: 'confirmed' }, { ...created, status: 'proposed', proposed_at: created.slot_at }] } : undefined))
    const rows = await screen.findAllByRole('row')
    const confirmed = rows.find((r) => within(r).queryByText('확정', { selector: '.pill' }))!
    expect(within(confirmed).queryByRole('button', { name: /취소/ })).toBeNull()
    expect(screen.getAllByRole('button', { name: /프리즈 취소/ })).toHaveLength(1)
    expect(screen.getByText(/확정된 면담은 취소할 수 없어요/)).toBeInTheDocument()
  })

  it('취소가 not_cancelable로 거절되면 안내 문구를 보여준다', async () => {
    await openPage(
      (req) => (req.url.endsWith('/meetings/me') ? { json: [created] } : undefined),
      (req) => (req.url.endsWith('/meetings/7/cancel') ? { status: 409, json: { code: 'not_cancelable' } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: /프리즈 취소/ }))
    await userEvent.click(within(await screen.findByRole('dialog', { name: '면담을 취소할까요?' })).getByRole('button', { name: '면담 취소' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Slack #pedago로 문의해 주세요')
  })
})


it('제안 시간을 표시하고 수락하면 확정으로 갱신한다', async () => {
  const proposal = { ...created, status: 'proposed', proposed_at: `${day}T06:07:00Z` }
  const calls = await openPage(
    (req) => req.url.endsWith('/meetings/me') ? { json: [proposal] } : undefined,
    (req) => req.url.endsWith('/meetings/7/accept') ? { json: { ...proposal, status: 'confirmed', slot_at: proposal.proposed_at } } : undefined,
  )
  expect(await screen.findByText(/제안:/)).toHaveTextContent('15:07')
  await userEvent.click(await screen.findByRole('button', { name: '제안 수락(확정하기)' }))
  expect(await screen.findByText('확정', { selector: '.pill' })).toBeInTheDocument()
  expect(calls.some(c => c.method === 'POST' && c.url.endsWith('/meetings/7/accept'))).toBe(true)

})
