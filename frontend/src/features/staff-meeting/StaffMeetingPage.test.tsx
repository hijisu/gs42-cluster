import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import { kstToIso } from '../../lib/datetime'
import type { StaffMeeting } from './api'

const members = [
  { id: 1, intra_id: 'staff', name: '모의 운영팀' },
  { id: 2, intra_id: 'staff2', name: '스태프 B' },
]
const types = [
  { id: 1, code: 'freeze', name: '프리즈', default_staff: { id: 2, name: '스태프 B' } },
  { id: 2, code: 'dormitory', name: '기숙사 이용', default_staff: null },
]
const meeting = (over: Partial<StaffMeeting> = {}): StaffMeeting => ({
  id: 5,
  type: { id: 1, code: 'freeze', name: '프리즈' },
  slot_at: '2030-10-15T06:00:00Z',
  content: '블랙홀 날짜 문의',
  notify_slack: true,
  status: 'pending',
  staff: null,
  location: '',
  proposed_at: null,
  student: { id: 3, intra_id: 'jisu', name: '지수' },
  staff_note: '',
  created_at: new Date().toISOString(),
  ...over,
})

const base: Handler = (req) => {
  if (req.url.endsWith('/staff/members')) return { json: members }
  if (req.url.endsWith('/staff/meeting-types') && req.method === 'GET') return { json: types }
  return undefined
}

const lists = (byStatus: Record<string, StaffMeeting[]>): Handler => (req) => {
  const m = req.url.match(/\/staff\/meetings\?status=(\w+)/)
  return m ? { json: byStatus[m[1]] ?? [] } : undefined
}

async function openPage(...handlers: Handler[]) {
  const calls = mockApi(asUser('staff'), ...handlers, base)
  renderAt('/staff/meeting')
  await screen.findByRole('heading', { name: '면담 관리' })
  return calls
}

describe('운영 면담 관리 화면', () => {
  it('탭에 건수를 보이고 요청 카드에 신청자·유형·희망 일시를 보여준다', async () => {
    await openPage(lists({ pending: [meeting(), meeting({ id: 6, content: '두 번째' })], proposed: [meeting({ id: 7, status: 'proposed' })] }))
    expect(await screen.findByRole('tab', { name: '신규 요청 2' })).toBeInTheDocument()
    expect(await screen.findByRole('tab', { name: '시간 조율 중 1' })).toBeInTheDocument()
    const card = await screen.findByTestId('meeting-5')
    expect(within(card).getByText('jisu')).toBeInTheDocument()
    expect(within(card).getByText('프리즈')).toBeInTheDocument()
    expect(within(card).getByText('블랙홀 날짜 문의')).toBeInTheDocument()
    expect(within(card).getByText('10.15 (화) 15:00')).toBeInTheDocument()
  })

  it('유형 기본 담당자를 기본 선택하고, 희망 일시로 확정하면 카드가 사라진다', async () => {
    let confirmed = false
    const calls = await openPage(
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/meetings/5/confirm') ? ((confirmed = true), { json: meeting({ status: 'confirmed' }) }) : undefined),
      (req) => (req.url.includes('status=pending') ? { json: confirmed ? [] : [meeting()] } : undefined),
    )
    const card = await screen.findByTestId('meeting-5')
    expect(within(card).getByLabelText('담당자')).toHaveValue('2')
    await userEvent.click(within(card).getByRole('button', { name: '희망 일시로 확정' }))
    await waitFor(() => expect(screen.queryByTestId('meeting-5')).toBeNull())
    expect(screen.getByText('새로 들어온 면담 요청이 없어요.')).toBeInTheDocument()
    const post = calls.find((c) => c.url.endsWith('/staff/meetings/5/confirm'))!
    expect(post.body).toEqual({ location: '1층 사무실 앞', staff_id: 2 })
  })

  it('확정이 실패하면 오류를 보이고 입력은 유지한다', async () => {
    await openPage(
      lists({ pending: [meeting()] }),
      (req) => (req.method === 'POST' ? { status: 409, json: { code: 'slot_unavailable' } } : undefined),
    )
    const card = await screen.findByTestId('meeting-5')
    const loc = within(card).getByLabelText('장소')
    await userEvent.clear(loc)
    await userEvent.type(loc, '2층 라운지')
    await userEvent.click(within(card).getByRole('button', { name: '희망 일시로 확정' }))
    expect(await within(card).findByRole('alert')).toHaveTextContent('이미 확정된 면담이 있어요')
    expect(within(card).getByLabelText('장소')).toHaveValue('2층 라운지')
  })

  it('장소가 비어 있으면 확정하지 않는다', async () => {
    const calls = await openPage(lists({ pending: [meeting()] }))
    const card = await screen.findByTestId('meeting-5')
    await userEvent.clear(within(card).getByLabelText('장소'))
    await userEvent.click(within(card).getByRole('button', { name: '희망 일시로 확정' }))
    expect(await within(card).findByText('장소를 입력해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })

  it('다른 시간을 제안한다', async () => {
    const calls = await openPage(
      lists({ pending: [meeting()] }),
      (req) => (req.method === 'POST' && req.url.endsWith('/propose') ? { json: meeting({ status: 'proposed' }) } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '다른 시간 제안' }))
    const dialog = await screen.findByRole('dialog', { name: '다른 시간 제안' })
    await userEvent.click(within(dialog).getByRole('button', { name: '시간 제안하기' }))
    expect(await within(dialog).findByText('날짜를 선택해 주세요.')).toBeInTheDocument()
    await userEvent.type(within(dialog).getByLabelText('날짜'), '2030-10-16')
    await userEvent.type(within(dialog).getByLabelText('시간'), '14:00')
    await userEvent.click(within(dialog).getByRole('button', { name: '시간 제안하기' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    const post = calls.find((c) => c.url.endsWith('/propose'))!
    expect(post.body).toEqual({ proposed_at: kstToIso('2030-10-16', '14:00') })
  })

  it('확정 탭은 담당자·장소를 읽기 전용으로 보여준다', async () => {
    await openPage(lists({ confirmed: [meeting({ status: 'confirmed', staff: { id: 2, name: '스태프 B' }, location: '1층 사무실 앞' })] }))
    await userEvent.click(await screen.findByRole('tab', { name: /^확정/ }))
    const card = await screen.findByTestId('meeting-5')
    expect(within(card).getByText('스태프 B')).toBeInTheDocument()
    expect(within(card).getByText('1층 사무실 앞')).toBeInTheDocument()
    expect(within(card).queryByRole('button', { name: '희망 일시로 확정' })).toBeNull()
  })

  it('유형별 기본 담당자를 저장한다', async () => {
    const calls = await openPage(
      lists({}),
      (req) => (req.method === 'PUT' && req.url.endsWith('/staff/meeting-types') ? { json: types } : undefined),
    )
    await userEvent.selectOptions(await screen.findByLabelText('기숙사 이용'), '1')
    await userEvent.click(screen.getByRole('button', { name: '기본 담당자 저장' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'PUT')).toBe(true))
    expect(calls.find((c) => c.method === 'PUT')!.body).toEqual([
      { id: 1, default_staff_id: 2 },
      { id: 2, default_staff_id: 1 },
    ])
  })

  it('내 면담 가능 시간을 설정해 저장한다', async () => {
    const calls = await openPage(lists({}), (req) => (req.method === 'PUT' && req.url.endsWith('/staff/availability') ? { json: { slots: [] } } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '내 면담 가능 시간 설정' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.click(await within(dialog).findByRole('button', { name: '10:00' }))
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'PUT')).toBe(true))
    const body = calls.find((c) => c.method === 'PUT')!.body as { from: string; to: string; slots: string[] }
    expect(body.from).toBe(body.to)
    expect(body.slots).toEqual([kstToIso(body.from, '10:00')])
  })
})
