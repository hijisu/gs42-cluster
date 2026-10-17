import { useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button, Chip } from '../../components'
import type { Book } from './api'
import { BookCard } from './BookCard'
import { BookDetailModal } from './BookDetailModal'
import { useBooks } from './hooks'
import { MyRequests } from './MyRequests'
import { ReportModal } from './ReportModal'
import { WishModal } from './WishForm'

/** 오아시스 도서(#28): 검색·카테고리, 상세, 분실·훼손 신고, 희망 도서 신청, 내 신청·신고 */
export function LibraryPage() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const q = params.get('q') ?? ''
  const category = params.get('category') ?? ''
  const [input, setInput] = useState(q)
  const [detail, setDetail] = useState<Book | null>(null)
  const [reporting, setReporting] = useState<Book | null>(null)
  const [wishing, setWishing] = useState(false)
  const [wished, setWished] = useState(false)
  const books = useBooks(q, category, true, page)

  // 검색어·카테고리는 주소에 두어 새로고침·뒤로가기·홈 검색 링크가 같은 결과를 보여 준다.
  const update = (next: { q?: string; category?: string }) => {
    const p = new URLSearchParams(params)
    p.delete('page')
    for (const [k, v] of Object.entries(next)) v ? p.set(k, v) : p.delete(k)
    setParams(p, { replace: true })
  }
  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    update({ q: input.trim() })
  }

  const data = books.data
  return (
    <>
      <div className="head">
        <div>
          <p className="label">03 · OASIS LIBRARY</p>
          <h1 className="h1" style={{ marginTop: 8 }}>오아시스 도서</h1>
          <p className="sub">오아시스에 비치된 약 500종의 책을 찾아보세요. 도서는 오아시스 안에서만 열람할 수 있어요.</p>
        </div>
        <Button onClick={() => { setWished(false); setWishing(true) }}>희망 도서 신청</Button>
      </div>
      {wished && <p role="status" className="info">신청했어요. 운영팀이 검토하면 '내 신청 · 신고'에 상태가 표시돼요.</p>}

      <div className="notice">
        <span className="stack" style={{ gap: 2 }}>
          <span className="label" style={{ color: 'var(--c-side-sub)' }}>열람 규칙</span>
          <span>
            오아시스 도서는 <b>(재)경산이노베이션아카데미</b>의 자산이에요. 클러스터·사물함·집으로 가져가지 말아 주세요. 장기 대출은 대구대 도서관을 이용해 주세요.
          </span>
        </span>
      </div>

      <div className="stack" style={{ gap: 14 }}>
        <form className="search-bar" role="search" onSubmit={onSubmit}>
          <label htmlFor="book-q" className="sr-only">도서 검색</label>
          <input id="book-q" className="input" type="search" placeholder="제목, 저자, 출판사, ISBN으로 검색" value={input} onChange={(e) => setInput(e.target.value)} />
          <Button type="submit">검색</Button>
        </form>
        <div className="chips" role="group" aria-label="분류">
          <Chip selected={category === ''} onClick={() => update({ category: '' })}>
            전체
          </Chip>
          {data?.categories.map((c) => (
            <Chip key={c} selected={category === c} onClick={() => update({ category: c })}>
              {c}
            </Chip>
          ))}
        </div>
      </div>

      <div className="split">
        <div className="stack" style={{ gap: 12, minWidth: 0 }}>
          {books.isPending && <p className="muted" role="status">불러오는 중…</p>}
          {books.isError && <p role="alert">도서를 불러오지 못했어요.</p>}
          {data && (
            <p className="muted small" role="status" aria-live="polite">
              {data.total === 0
                ? '검색 결과가 없어요. 다른 검색어를 써 보세요.'
                : data.total > data.results.length
                  ? `${data.total}종 중 ${data.results.length}종 표시`
                  : `${data.total}종`}
            </p>
          )}
          {data && data.total > 20 && <nav aria-label="도서 페이지" className="row">
            <Button variant="secondary" disabled={page <= 1 || books.isPlaceholderData} onClick={() => { const p = new URLSearchParams(params); p.set('page', String(page - 1)); setParams(p) }}>이전</Button>
            <span>{page} / {Math.ceil(data.total / 20)} 페이지</span>
            <Button variant="secondary" disabled={page >= Math.ceil(data.total / 20) || books.isPlaceholderData} onClick={() => { const p = new URLSearchParams(params); p.set('page', String(page + 1)); setParams(p) }}>다음</Button>
          </nav>}
          <div className="g4 book-grid">
            {data?.results.map((b) => (
              <BookCard key={b.id} book={b} onOpen={setDetail} onReport={setReporting} />
            ))}
          </div>
        </div>
        <div className="col">
          <MyRequests />
        </div>
      </div>

      <BookDetailModal
        book={detail}
        onClose={() => setDetail(null)}
        onReport={(b) => {
          setDetail(null)
          setReporting(b)
        }}
      />
      <WishModal open={wishing} onClose={() => setWishing(false)} onDone={() => { setWishing(false); setWished(true) }} />
      <ReportModal book={reporting} onClose={() => setReporting(null)} />
    </>
  )
}
