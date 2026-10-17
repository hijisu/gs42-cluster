import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import type { Book, BookReport, BookWish } from './api'

const book = (over: Partial<Book> = {}): Book => ({
  id: 1, code: 'B-1', title: '클린 코드', author: '로버트 마틴', publisher: '인사이트', isbn: '', category: '컴퓨터/IT',
  quantity: 2, description: '', cover_url: '', link_url: '', pub_date: '', location: 'A-2', ...over,
})
const wish = (over: Partial<BookWish> = {}): BookWish => ({
  id: 7, title: '쿠버네티스 인 액션', author: '', reason: '실습용', link_url: '', status: 'requested', staff_note: '',
  created_at: '2026-10-08T01:00:00Z', requester: { intra_id: 'alice', name: '앨리스' }, ...over,
})
const report = (over: Partial<BookReport> = {}): BookReport => ({
  id: 3, book_id: 1, book_code: 'B-1', book_title: '컴퓨터 네트워킹', kind: 'lost', detail: '서가에 없음', status: 'received',
  created_at: '2026-10-08T01:00:00Z', reporter: { intra_id: 'bob', name: '밥' }, ...over,
})

const get = (suffix: string, json: unknown): Handler => (req) => (req.method === 'GET' && req.url.includes(suffix) ? { json } : undefined)
const search = (books: Book[]) => get('/books/?q=', { total: books.length, categories: ['컴퓨터/IT'], results: books })

async function openPage(...handlers: Handler[]) {
  const calls = mockApi(asUser('staff'), ...handlers)
  renderAt('/staff/library')
  await screen.findByRole('heading', { name: '도서 관리' })
  return calls
}

describe('운영 도서 관리 화면', () => {
  it('도서 표와 총 권수를 보여주고 검색어를 API로 보낸다', async () => {
    const calls = await openPage(search([book()]), get('/staff/book-wishes', []), get('/staff/book-reports', []))
    const table = await screen.findByRole('table', { name: '도서 목록' })
    const row = within(table).getByText('클린 코드').closest('tr') as HTMLElement
    expect(within(row).getByText('A-2')).toBeInTheDocument()
    expect(within(row).getByText('2권')).toBeInTheDocument()
    expect(screen.getByText('총 1종')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('도서 검색'), '마틴')
    await waitFor(() => expect(calls.some((c) => c.url.includes('q=%EB%A7%88%ED%8B%B4'))).toBe(true))
  })

  it('도서를 추가한다', async () => {
    const created = book({ id: 9, code: 'N-1', title: '새 책' })
    const calls = await openPage(
      search([book()]),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/books') ? { status: 201, json: created } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '도서 추가' }))
    const dialog = screen.getByRole('dialog', { name: '도서 추가' })
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    expect(within(dialog).getAllByText('필수 항목이에요.')).toHaveLength(3)

    await userEvent.type(within(dialog).getByLabelText('도서 코드'), 'N-1')
    await userEvent.type(within(dialog).getByLabelText('제목'), '새 책')
    await userEvent.type(within(dialog).getByLabelText('분류'), '인문')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    const post = calls.find((c) => c.method === 'POST')
    expect(post?.body).toMatchObject({ code: 'N-1', title: '새 책', category: '인문', quantity: 1 })
  })

  it('중복 코드 오류를 안내한다', async () => {
    await openPage(
      search([book()]),
      (req) => (req.method === 'POST' && req.url.endsWith('/staff/books') ? { status: 409, json: { code: 'duplicate_book' } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '도서 추가' }))
    const dialog = screen.getByRole('dialog', { name: '도서 추가' })
    await userEvent.type(within(dialog).getByLabelText('도서 코드'), 'B-1')
    await userEvent.type(within(dialog).getByLabelText('제목'), '클린 코드')
    await userEvent.type(within(dialog).getByLabelText('분류'), '컴퓨터/IT')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    expect(await within(dialog).findByRole('alert')).toHaveTextContent('이미 있는 도서 코드예요.')
  })

  it('도서를 수정할 때 도서 코드는 바꿀 수 없고 서버에 보내지 않는다', async () => {
    const calls = await openPage(
      search([book()]),
      (req) => (req.method === 'PATCH' ? { json: book({ location: 'B-1' }) } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '클린 코드 수정' }))
    const dialog = screen.getByRole('dialog', { name: '도서 수정' })
    expect(within(dialog).getByLabelText('도서 코드')).toBeDisabled()
    const loc = within(dialog).getByLabelText('서가 위치')
    await userEvent.clear(loc)
    await userEvent.type(loc, 'B-1')
    await userEvent.click(within(dialog).getByRole('button', { name: '저장' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'PATCH')).toBe(true))
    const patch = calls.find((c) => c.method === 'PATCH')
    expect(patch?.url).toMatch(/\/staff\/books\/1$/)
    expect(patch?.body).toMatchObject({ location: 'B-1', quantity: 2 })
    expect(patch?.body).not.toHaveProperty('code')
  })

  it('삭제는 확인을 거친 뒤에만 보낸다', async () => {
    const calls = await openPage(search([book()]), (req) => (req.method === 'DELETE' ? { status: 204 } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '클린 코드 삭제' }))
    expect(calls.some((c) => c.method === 'DELETE')).toBe(false)
    await userEvent.click(within(screen.getByRole('dialog', { name: '도서 삭제' })).getByRole('button', { name: '삭제' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'DELETE' && c.url.endsWith('/staff/books/1'))).toBe(true))
  })

  it('희망 도서: 접수 → 검토 중, 검토 중 → 구매 확정', async () => {
    const calls = await openPage(
      search([]),
      get('/staff/book-wishes', [wish(), wish({ id: 8, title: '검토 중인 책', status: 'approved' })]),
      (req) => (req.method === 'PATCH' ? { json: wish() } : undefined),
    )
    const first = await screen.findByRole('listitem', { name: '희망 도서 쿠버네티스 인 액션' })
    expect(within(first).getByText('alice', { exact: false })).toBeInTheDocument()
    await userEvent.click(within(first).getByRole('button', { name: '쿠버네티스 인 액션 검토 중으로' }))
    await userEvent.click(screen.getByRole('button', { name: '검토 중인 책 구매 확정' }))
    await waitFor(() => expect(calls.filter((c) => c.method === 'PATCH')).toHaveLength(2))
    const [a, b] = calls.filter((c) => c.method === 'PATCH')
    expect(a.url).toMatch(/book-wishes\/7$/)
    expect(a.body).toMatchObject({ status: 'approved' })
    expect(b.body).toMatchObject({ status: 'purchased' })
  })

  it('희망 도서 반려는 사유가 필요하고, 이미 비치됨은 사유를 자동으로 보낸다', async () => {
    const calls = await openPage(
      search([]),
      get('/staff/book-wishes', [wish()]),
      (req) => (req.method === 'PATCH' ? { json: wish({ status: 'rejected' }) } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '쿠버네티스 인 액션 반려' }))
    const dialog = screen.getByRole('dialog', { name: '희망 도서 반려' })
    await userEvent.click(within(dialog).getByRole('button', { name: '반려' }))
    expect(within(dialog).getByText('반려 사유를 입력해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'PATCH')).toBe(false)
    await userEvent.type(within(dialog).getByLabelText('반려 사유'), '예산 초과')
    await userEvent.click(within(dialog).getByRole('button', { name: '반려' }))
    await waitFor(() => expect(calls.find((c) => c.method === 'PATCH')?.body).toMatchObject({ status: 'rejected', note: '예산 초과' }))

    await userEvent.click(await screen.findByRole('button', { name: '쿠버네티스 인 액션 이미 비치됨' }))
    await waitFor(() => expect(calls.filter((c) => c.method === 'PATCH')).toHaveLength(2))
    expect(calls.filter((c) => c.method === 'PATCH')[1].body).toMatchObject({ status: 'rejected', note: '이미 비치된 도서입니다' })
  })

  it('분실·훼손 신고는 처리 완료 전까지만 보이고 처리 완료를 보낸다', async () => {
    const calls = await openPage(
      search([]),
      get('/staff/book-reports', [report(), report({ id: 4, book_title: '끝난 신고', status: 'resolved' })]),
      (req) => (req.method === 'POST' && req.url.endsWith('/resolve') ? { json: report({ status: 'resolved' }) } : undefined),
    )
    const item = await screen.findByRole('listitem', { name: '신고 컴퓨터 네트워킹' })
    expect(within(item).getByText('분실')).toBeInTheDocument()
    expect(screen.queryByText('끝난 신고')).not.toBeInTheDocument()
    await userEvent.click(within(item).getByRole('button', { name: '컴퓨터 네트워킹 처리 완료' }))
    await waitFor(() => expect(calls.some((c) => c.method === 'POST' && c.url.endsWith('/book-reports/3/resolve'))).toBe(true))
  })

  it('처리된 항목을 다시 처리하면 안내한다', async () => {
    await openPage(
      search([]),
      get('/staff/book-reports', [report()]),
      (req) => (req.method === 'POST' ? { status: 409, json: { code: 'invalid_transition' } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '컴퓨터 네트워킹 처리 완료' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('이미 처리된 항목이에요')
  })
})


it('운영 도서 목록에서 페이지를 이동하고 검색하면 첫 페이지로 돌아간다', async () => {
  const calls = await openPage(req => req.url.includes('/books/') ? { json: { total: 41, categories: [], results: [book()] } } : undefined)
  await userEvent.click(await screen.findByRole('button', { name: '다음' }))
  await waitFor(() => expect(calls.some(c => c.url.includes('page=2'))).toBe(true))
  await userEvent.type(screen.getByLabelText('도서 검색'), '코드')
  await waitFor(() => expect(calls.some(c => decodeURIComponent(c.url).includes('q=코드') && c.url.includes('page=1'))).toBe(true))
  expect(screen.getByRole('button', { name: '이전' })).toBeDisabled()
})
