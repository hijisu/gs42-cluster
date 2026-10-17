import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { asUser, mockApi, renderAt, type Handler } from '../../test-utils'
import type { Book, BookReport, BookSearch, BookWish } from './api'
import { coverIndex } from './BookCard'

const book = (over: Partial<Book> = {}): Book => ({
  id: 1,
  code: 'GSIA-IT-001',
  title: '클린 코드 Clean Code',
  author: '로버트 C. 마틴',
  publisher: '인사이트',
  isbn: '9788966260959',
  category: '컴퓨터/IT',
  quantity: 2,
  description: '애자일 소프트웨어 장인 정신',
  cover_url: '',
  link_url: 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=1',
  pub_date: '2013-12-24',
  ...over,
})
const books = [book(), book({ id: 2, code: 'GSIA-HU-002', title: '사피엔스', author: '유발 하라리', category: '인문', quantity: 1, cover_url: 'https://image.example/c.jpg', isbn: '', link_url: '' })]
const wish = (over: Partial<BookWish> = {}): BookWish => ({ id: 1, title: '이것이 리눅스다', author: '우재남', reason: '', link_url: '', status: 'requested', staff_note: '', created_at: '2026-10-17T00:00:00Z', ...over })
const report = (over: Partial<BookReport> = {}): BookReport => ({ id: 1, book_id: 1, book_code: 'GSIA-IT-001', book_title: '클린 코드 Clean Code', kind: 'lost', detail: '', status: 'received', created_at: '2026-10-17T00:00:00Z', ...over })

const search = (over: Partial<BookSearch> = {}): Handler => (req) =>
  req.method === 'GET' && /\/books\/(\?|$)/.test(req.url)
    ? { json: { total: over.total ?? books.length, categories: ['컴퓨터/IT', '인문'], results: over.results ?? books } }
    : undefined

async function openPage(path = '/library', ...handlers: Handler[]) {
  const calls = mockApi(asUser('student'), ...handlers)
  renderAt(path)
  await screen.findByRole('heading', { level: 1, name: '오아시스 도서' })
  return calls
}
const urls = (calls: { url: string }[]) => calls.map((c) => decodeURIComponent(c.url))

describe('오아시스 도서 화면', () => {
  it('도서 카드(제목·저자·비치 수)와 분류 chip, 총 건수를 보여준다', async () => {
    await openPage('/library', search())
    const card = (await screen.findByRole('button', { name: '클린 코드 Clean Code' })).closest('article') as HTMLElement
    expect(within(card).getAllByText('로버트 C. 마틴').length).toBeGreaterThanOrEqual(1) // 표지 대체 문구 + 본문
    expect(within(card).getByText('2권 비치')).toBeInTheDocument()
    expect(within(card).queryByText(/서가/)).toBeNull()
    expect(screen.getByRole('button', { name: '인문' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '전체', pressed: true })).toBeInTheDocument()
    expect(await screen.findByText('2종')).toBeInTheDocument()
  })

  it('표지가 있으면 no-referrer 이미지, 없으면 색 표지로 대체한다', async () => {
    await openPage('/library', search())
    const withCover = (await screen.findByRole('button', { name: '사피엔스' })).closest('article') as HTMLElement
    const img = withCover.querySelector('img')!
    expect(img).toHaveAttribute('src', 'https://image.example/c.jpg')
    expect(img).toHaveAttribute('referrerpolicy', 'no-referrer')
    const without = screen.getByRole('button', { name: '클린 코드 Clean Code' }).closest('article') as HTMLElement
    expect(without.querySelector('img')).toBeNull()
    expect(without.querySelector('.book-cover-fallback')).toHaveClass(`cover-${coverIndex('GSIA-IT-001')}`)
  })

  it('결과가 200건 상한을 넘으면 전체 수와 표시 수를 함께 안내한다', async () => {
    await openPage('/library', search({ total: 518 }))
    expect(await screen.findByText(/518종 중 2종 표시/)).toBeInTheDocument()
  })

  it('결과가 없으면 안내 문구를 보여준다', async () => {
    await openPage('/library', search({ total: 0, results: [] }))
    expect(await screen.findByText('검색 결과가 없어요. 다른 검색어를 써 보세요.')).toBeInTheDocument()
  })

  it('검색어와 분류가 서버 요청과 주소에 반영된다', async () => {
    const calls = await openPage('/library', search())
    await userEvent.type(await screen.findByLabelText('도서 검색'), '클린')
    await userEvent.click(screen.getByRole('button', { name: '검색' }))
    await waitFor(() => expect(urls(calls).some((u) => u.includes('/books/?q=클린'))).toBe(true))
    await userEvent.click(screen.getByRole('button', { name: '인문' }))
    await waitFor(() => expect(urls(calls).some((u) => u.includes('q=클린') && u.includes('category=인문'))).toBe(true))
    expect(await screen.findByRole('button', { name: '인문', pressed: true })).toBeInTheDocument()
  })

  it('주소의 ?q= 검색어로 바로 검색한다(홈 통합 검색 링크)', async () => {
    const calls = await openPage(`/library?q=${encodeURIComponent('사피')}`, search())
    expect(urls(calls).some((u) => u.includes('/books/?q=사피'))).toBe(true)
    expect(screen.getByLabelText('도서 검색')).toHaveValue('사피')
  })

  it('상세 보기: 서지 정보·소개와 외부 링크(새 탭, noopener)를 보여준다', async () => {
    await openPage('/library', search())
    await userEvent.click(await screen.findByRole('button', { name: '클린 코드 Clean Code' }))
    const dialog = await screen.findByRole('dialog', { name: '클린 코드 Clean Code' })
    expect(within(dialog).getByText('애자일 소프트웨어 장인 정신')).toBeInTheDocument()
    expect(within(dialog).getByText('인사이트 · 2013-12-24')).toBeInTheDocument()
    expect(within(dialog).getByText('9788966260959')).toBeInTheDocument()
    const link = within(dialog).getByRole('link', { name: /서점에서 자세히 보기/ })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link.getAttribute('rel')).toMatch(/noopener/)
  })

  it('분실 신고: 도서 id·유형을 보내고 접수 안내를 보여준다', async () => {
    const calls = await openPage('/library', search(), (req) => (req.method === 'POST' && req.url.endsWith('/books/reports') ? { status: 201, json: report() } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '클린 코드 Clean Code 신고' }))
    const dialog = await screen.findByRole('dialog', { name: '분실 · 훼손 신고' })
    await userEvent.click(within(dialog).getByRole('button', { name: '신고하기' }))
    expect(await within(dialog).findByText(/신고가 접수됐어요/)).toBeInTheDocument()
    expect(calls.find((c) => c.url.endsWith('/books/reports'))!.body).toEqual({ book_id: 1, kind: 'lost', detail: '' })
  })

  it('훼손 신고는 내용이 없으면 보내지 않고, 서버 오류 코드를 안내한다', async () => {
    const calls = await openPage('/library', search(), (req) => (req.method === 'POST' ? { status: 400, json: { code: 'invalid_report' } } : undefined))
    await userEvent.click(await screen.findByRole('button', { name: '클린 코드 Clean Code 신고' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.click(within(dialog).getByRole('button', { name: '훼손' }))
    await userEvent.click(within(dialog).getByRole('button', { name: '신고하기' }))
    expect(await within(dialog).findByText('훼손된 내용을 적어 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
    await userEvent.type(within(dialog).getByLabelText('훼손 내용'), '표지가 찢어짐')
    await userEvent.click(within(dialog).getByRole('button', { name: '신고하기' }))
    expect(await within(dialog).findByRole('alert')).toHaveTextContent('훼손 내용을 적어 주세요')
    expect(calls.find((c) => c.method === 'POST')!.body).toEqual({ book_id: 1, kind: 'damaged', detail: '표지가 찢어짐' })
  })

  it('상세에서 바로 신고 화면으로 넘어간다', async () => {
    await openPage('/library', search())
    await userEvent.click(await screen.findByRole('button', { name: '클린 코드 Clean Code' }))
    await userEvent.click(within(await screen.findByRole('dialog', { name: '클린 코드 Clean Code' })).getByRole('button', { name: '분실·훼손 신고' }))
    expect(await screen.findByRole('dialog', { name: '분실 · 훼손 신고' })).toBeInTheDocument()
  })

  it('희망 도서 신청: 도서명이 필수이고, 신청하면 내 내역에 반영된다', async () => {
    let posted = false
    const calls = await openPage(
      '/library',
      search(),
      (req) => (req.method === 'POST' && req.url.endsWith('/books/wishes') ? ((posted = true), { status: 201, json: wish() }) : undefined),
      (req) => (req.url.endsWith('/books/my-requests') ? { json: { reports: [], wishes: posted ? [wish()] : [] } } : undefined),
    )
    await userEvent.click(await screen.findByRole('button', { name: '신청하기' }))
    expect(await screen.findByText('도서명을 입력해 주세요.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)

    await userEvent.type(screen.getByLabelText('도서명'), '이것이 리눅스다')
    await userEvent.type(screen.getByLabelText('저자 · 출판사'), '우재남')
    await userEvent.click(screen.getByRole('button', { name: '신청하기' }))
    expect(await screen.findByText(/신청했어요/)).toBeInTheDocument()
    expect(calls.find((c) => c.method === 'POST')!.body).toEqual({ title: '이것이 리눅스다', author: '우재남', reason: '', link_url: '' })
    const item = await screen.findByTestId('wish-1')
    expect(within(item).getByText('접수', { selector: '.pill' })).toBeInTheDocument()
  })

  it('내 신청·신고: 상태 문구와 반려 사유를 보여준다', async () => {
    await openPage(
      '/library',
      search(),
      (req) =>
        req.url.endsWith('/books/my-requests')
          ? { json: { wishes: [wish({ status: 'rejected', staff_note: '이미 소장 중' }), wish({ id: 2, title: '다른 책', status: 'purchased' })], reports: [report({ status: 'resolved' }), report({ id: 2, kind: 'damaged' })] } }
          : undefined,
    )
    const rejected = await screen.findByTestId('wish-1')
    expect(within(rejected).getByText('반려', { selector: '.pill' })).toBeInTheDocument()
    expect(within(rejected).getByText('반려 사유: 이미 소장 중')).toBeInTheDocument()
    expect(within(screen.getByTestId('wish-2')).getByText('구매 확정', { selector: '.pill' })).toBeInTheDocument()
    expect(within(screen.getByTestId('report-1')).getByText('처리 완료', { selector: '.pill' })).toBeInTheDocument()
    const damaged = screen.getByTestId('report-2')
    expect(within(damaged).getByText(/훼손/)).toBeInTheDocument()
    expect(within(damaged).getByText('확인 중', { selector: '.pill' })).toBeInTheDocument()
  })

  it('내역이 없으면 빈 상태, 도서 조회가 실패하면 오류를 보여준다', async () => {
    await openPage('/library', (req) => (req.method === 'GET' && /\/books\/(\?|$)/.test(req.url) ? { status: 500, json: {} } : undefined))
    expect(await screen.findByText('신청하거나 신고한 내역이 없어요.')).toBeInTheDocument()
    expect(await screen.findByText('도서를 불러오지 못했어요.')).toBeInTheDocument()
  })
})

describe('coverIndex', () => {
  it('같은 코드는 항상 같은 1~8번 표지를 고른다', () => {
    expect(coverIndex('GSIA-IT-001')).toBe(coverIndex('GSIA-IT-001'))
    for (const c of ['A', 'GSIA-HU-002', '한글코드', '']) {
      expect(coverIndex(c)).toBeGreaterThanOrEqual(1)
      expect(coverIndex(c)).toBeLessThanOrEqual(8)
    }
  })
})
