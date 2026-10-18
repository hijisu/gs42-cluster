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

async function openCreate() {
  await userEvent.click(await screen.findByRole('button', { name: '+ 교육과정 등록' }))
  return screen.findByRole('dialog', { name: '새 교육과정 등록' })
}

describe('운영 교육과정·후기 관리 화면', () => {
  it('과정 표에 기간·참여·작성률·상태를 보여준다', async () => {
    await openPage(list([course(), upcoming, closed]))
    const table = await screen.findByRole('table', { name: '교육과정 목록' })
    const row = within(table).getByText('서울대학교 파이썬 AI 교육').closest('tr') as HTMLElement
    expect(within(row).getByText('2026.10.05–10.14')).toBeInTheDocument()
    expect(within(row).getByText('4명')).toBeInTheDocument()
    expect(within(row).getByText('25%')).toBeInTheDocument()
    expect(within(row).getByText('후기 수집 중')).toBeInTheDocument()
    expect(within(table).getByText('시작 전')).toBeInTheDocument()
    expect(within(table).getByText('종료', { selector: '.pill' })).toBeInTheDocument()
  })

  it('과정을 등록한다: 참여 intra ID(Enter)를 칩으로 모아 보낸다', async () => {
    const calls = await openPage(
      list([]),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/courses') ? { status: 201, json: course({ id: 9, name: '새 과정', participant_count: 2 }) } : undefined),
    )
    const dialog = await openCreate()
    await userEvent.type(within(dialog).getByLabelText('과정명'), '새 과정')
    await userEvent.type(within(dialog).getByLabelText('시작일'), '2026-11-18')
    await userEvent.type(within(dialog).getByLabelText('종료일'), '2026-11-26')
    await userEvent.type(within(dialog).getByLabelText('장소'), '유니버스룸')
    await userEvent.type(within(dialog).getByLabelText('참여 학생'), 'Alice, bob{Enter}')
    expect(within(dialog).getByText('alice')).toBeInTheDocument()
    expect(within(dialog).getByText('bob')).toBeInTheDocument()
    await userEvent.type(within(dialog).getByLabelText('참여 학생'), 'carol')
    await userEvent.click(within(dialog).getByRole('button', { name: '추가' }))
    expect(within(dialog).getByText('carol')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: '과정 등록' }))

    expect(await screen.findByText(/참여 2명 · 후기 게시판이 만들어졌어요/)).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(calls.find((c) => c.method === 'POST')!.body).toEqual({
      name: '새 과정',
      start_date: '2026-11-18',
      end_date: '2026-11-26',
      location: '유니버스룸',
      intro: '',
      review_deadline: null,
      intra_ids: ['alice', 'bob', 'carol'],
      csv: '',
    })
  })

  it('CSV 파일을 읽어 함께 보낸다', async () => {
    const calls = await openPage(list([]), (req) => (req.method === 'POST' ? { status: 201, json: course({ id: 9 }) } : undefined))
    const dialog = await openCreate()
    await userEvent.type(within(dialog).getByLabelText('과정명'), '과정')
    await userEvent.type(within(dialog).getByLabelText('시작일'), '2026-11-18')
    await userEvent.type(within(dialog).getByLabelText('종료일'), '2026-11-26')
    await userEvent.upload(within(dialog).getByLabelText('CSV 파일 선택'), new File(['intra_id\ncarol,dave'], 'students.csv', { type: 'text/csv' }))
    expect(await within(dialog).findByText('CSV: students.csv')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: '과정 등록' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'POST')).toBe(true))
    expect((calls.find((c) => c.method === 'POST')!.body as { csv: string }).csv).toBe('intra_id\ncarol,dave')
  })

  it('필수값이 비면 등록하지 않고, 서버 오류 코드를 안내한다', async () => {
    const calls = await openPage(list([]), (req) => (req.method === 'POST' ? { status: 400, json: { code: 'invalid_intra_id' } } : undefined))
    const dialog = await openCreate()
    await userEvent.click(within(dialog).getByRole('button', { name: '과정 등록' }))
    expect(await within(dialog).findByText('과정명을 입력해 주세요.')).toBeInTheDocument()
    expect(within(dialog).getByText('시작일을 선택해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)

    await userEvent.type(within(dialog).getByLabelText('과정명'), '과정')
    await userEvent.type(within(dialog).getByLabelText('시작일'), '2026-11-18')
    await userEvent.type(within(dialog).getByLabelText('종료일'), '2026-11-26')
    await userEvent.click(within(dialog).getByRole('button', { name: '과정 등록' }))
    expect(await within(dialog).findByText(/intra ID 형식이 올바르지 않아요/)).toBeInTheDocument()
  })

  async function openRequest(name = '서울대학교 파이썬 AI 교육') {
    await userEvent.click(await screen.findByRole('button', { name: `${name} 후기 요청` }))
    return screen.findByRole('dialog', { name: '후기 요청 보내기' })
  }

  it('후기 요청: 작성 완료/미작성 수를 보이고 미작성자에게만 보낸다', async () => {
    const calls = await openPage(
      list([course(), upcoming]),
      (req) => (req.url.endsWith('/review-request') ? { json: { course_id: 4, target: 'pending', recipient_count: 3, recipients: ['a', 'b', 'c'] } } : undefined),
    )
    const form = await openRequest()
    expect(within(form).getByLabelText('교육과정')).toHaveValue('서울대학교 파이썬 AI 교육')
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
    const form = await openRequest()
    const deadline = within(form).getByLabelText('작성 마감')
    await userEvent.clear(deadline)
    await userEvent.type(deadline, '2099-12-31')
    await userEvent.click(within(form).getByRole('button', { name: '전체에게 보내기' }))
    expect(await within(form).findByText('4명에게 후기 요청을 보냈어요.')).toBeInTheDocument()
    const order = calls.filter((c) => c.method === 'PATCH' || c.url.endsWith('/review-request')).map((c) => c.method)
    expect(order).toEqual(['PATCH', 'POST'])
    expect(calls.find((c) => c.method === 'PATCH')!.body).toEqual({ review_deadline: '2099-12-31' })
  })

  it('후기를 받는 중이 아닌 과정에는 후기 요청 버튼이 없다', async () => {
    await openPage(list([upcoming, closed]))
    expect(await screen.findByRole('table', { name: '교육과정 목록' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /후기 요청/ })).toBeNull()
  })

  it('등록은 팝업에서 하고 상태 선택이 없다. 페이지 하단 폼은 없다', async () => {
    await openPage(list([]))
    expect(screen.queryByRole('button', { name: '과정 등록' })).toBeNull()
    const dialog = await openCreate()
    expect(within(dialog).queryByLabelText('상태')).toBeNull()
    expect(within(dialog).getByLabelText('시작일').closest('.g2')).toContainElement(within(dialog).getByLabelText('종료일'))
    expect(screen.queryByRole('button', { name: /후기 열기/ })).toBeNull()
  })

  it('과정을 수정해 저장한다(상태는 보내지 않는다)', async () => {
    const detail = { ...course(), participants: [{ intra_id: 'alice', reviewed: true }, { intra_id: 'bob', reviewed: false }] }
    const calls = await openPage(
      list([course()]),
      (req) => (req.method === 'GET' && req.url.endsWith('/staff/courses/4') ? { json: detail } : undefined),
      (req) => (req.method === 'PATCH' ? { json: course({ name: '이름 변경' }) } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '서울대학교 파이썬 AI 교육 수정' }))
    const dialog = await screen.findByRole('dialog')
    const name = await within(dialog).findByLabelText('과정명')
    await userEvent.clear(name)
    await userEvent.type(name, '이름 변경')
    await userEvent.click(within(dialog).getByRole('button', { name: '정보 저장' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'PATCH')).toBe(true))
    const patch = calls.find((c) => c.method === 'PATCH')!
    expect(patch.url).toMatch(/\/staff\/courses\/4$/)
    expect(patch.body).toMatchObject({ name: '이름 변경', start_date: '2026-10-05', end_date: '2026-10-14' })
    expect(patch.body).not.toHaveProperty('status')
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  })

  it('참여 학생을 알파벳 순으로 보여주고, 10명을 넘으면 검색할 수 있다', async () => {
    const few = { ...course(), participants: [{ intra_id: 'bob', reviewed: false }, { intra_id: 'alice', reviewed: true }] }
    await openPage(list([course()]), (req) => (req.method === 'GET' && req.url.endsWith('/staff/courses/4') ? { json: few } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '서울대학교 파이썬 AI 교육 수정' }))
    const dialog = await screen.findByRole('dialog')
    await within(dialog).findByTestId('participant-alice')
    expect(within(dialog).getAllByTestId(/^participant-/).map((e) => e.getAttribute('data-testid'))).toEqual(['participant-alice', 'participant-bob'])
    expect(within(dialog).queryByLabelText('참여 학생 검색')).toBeNull()
  })

  it('참여 학생이 많으면 검색으로 걸러 본다', async () => {
    const ids = ['zed', ...Array.from({ length: 11 }, (_, i) => `user${String(i).padStart(2, '0')}`)]
    const many = { ...course(), participants: ids.map((intra_id) => ({ intra_id, reviewed: false })) }
    await openPage(list([course()]), (req) => (req.method === 'GET' && req.url.endsWith('/staff/courses/4') ? { json: many } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '서울대학교 파이썬 AI 교육 수정' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.type(await within(dialog).findByLabelText('참여 학생 검색'), 'ZE')
    expect(within(dialog).getAllByTestId(/^participant-/)).toHaveLength(1)
    expect(within(dialog).getByText('12명 중 1명')).toBeInTheDocument()
  })

  it('수정 폼에서 종료일이 시작일보다 이르면 저장하지 않는다', async () => {
    const calls = await openPage(list([course()]), (req) => (req.method === 'GET' && req.url.endsWith('/staff/courses/4') ? { json: { ...course(), participants: [] } } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '서울대학교 파이썬 AI 교육 수정' }))
    const dialog = await screen.findByRole('dialog')
    const end = await within(dialog).findByLabelText('종료일')
    await userEvent.clear(end)
    await userEvent.type(end, '2026-10-01')
    await userEvent.click(within(dialog).getByRole('button', { name: '정보 저장' }))
    expect(await within(dialog).findByText('종료일은 시작일 이후여야 해요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'PATCH')).toBe(false)
  })

  it('수정 모달에서 CSV 파일로 참여 학생을 추가한다', async () => {
    const detail = { ...course(), participants: [{ intra_id: 'alice', reviewed: false }] }
    const calls = await openPage(
      list([course()]),
      (req) => (req.method === 'GET' && req.url.endsWith('/staff/courses/4') ? { json: detail } : undefined),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/courses/4/participants') ? { json: { added: ['carol', 'dave'], existing: [], course: detail } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '서울대학교 파이썬 AI 교육 수정' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.upload(await within(dialog).findByLabelText('CSV 파일 선택'), new File(['intra_id\ncarol,dave'], 's.csv', { type: 'text/csv' }))
    expect(await within(dialog).findByText(/2명을 추가했어요/)).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'POST')!.body).toEqual({ intra_ids: [], csv: 'intra_id\ncarol,dave' })
  })

  it('참여 학생을 추가하고, 후기 쓴 참여자는 확인 후 제거한다', async () => {
    const detail = { ...course(), participants: [{ intra_id: 'alice', reviewed: true }, { intra_id: 'bob', reviewed: false }] }
    const calls = await openPage(
      list([course()]),
      (req) => (req.method === 'GET' && req.url.endsWith('/staff/courses/4') ? { json: detail } : undefined),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/courses/4/participants') ? { json: { added: ['carol'], existing: ['bob'], course: detail } } : undefined),
      (req) => (req.method === 'DELETE' && req.url.endsWith('/staff/courses/4/participants/alice') ? { json: { had_review: true, course: detail } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '서울대학교 파이썬 AI 교육 수정' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.type(await within(dialog).findByLabelText('추가할 intra ID'), 'Carol, bob')
    await userEvent.click(within(dialog).getByRole('button', { name: '추가' }))
    expect(await within(dialog).findByText(/1명을 추가했어요\. 이미 있는 1명은 건너뛰었어요/)).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'POST')!.body).toEqual({ intra_ids: ['carol', 'bob'] })

    await userEvent.click(within(dialog).getByRole('button', { name: 'alice 제거' }))
    expect(within(dialog).getByText(/이미 후기를 썼어요/)).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'DELETE')).toBe(false)
    await userEvent.click(within(dialog).getByRole('button', { name: '제거 확인' }))
    expect(await within(dialog).findByText(/후기는 남고 작성률에서만 빠져요/)).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'DELETE')).toBe(true)
  })
})
