import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import type { Meeting } from './api'
import { kstDateFromToday } from '../../lib/datetime'

const types = [
  { id: 1, code: 'freeze', name: '프리즈' },
  { id: 2, code: 'dormitory', name: '기숙사 이용' },
]
// 내일 KST 15:00 (= 06:00Z) 과 16:00 슬롯
const day = kstDateFromToday(1)
const slots = [
  { start_at: `${day}T06:00:00Z`, available: true, remaining: 1 },
  { start_at: `${day}T07:00:00Z`, available: false, remaining: 0 },
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
  it('유형 chip, 가능/마감 격자, 이용 안내 문구를 보여준다', async () => {
    await openPage()
    expect(await screen.findByRole('button', { name: '프리즈' })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /15:00 가능/ })).toBeInTheDocument()
    expect(screen.getByLabelText(/16:00 마감/)).toBeInTheDocument()
    expect(screen.getByText('#pedago 이용 안내')).toBeInTheDocument()
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
