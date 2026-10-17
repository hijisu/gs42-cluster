import { useState } from 'react'
import { Button, Card, Pill } from '../../components'
import type { Book } from './api'

/** 코드 문자열로 고르는 대체 표지 번호(1~8) */
export function coverIndex(code: string): number {
  let h = 0
  for (const ch of code) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return (h % 8) + 1
}

/** 표지 이미지. 없거나 불러오지 못하면 시안의 색 표지(제목·저자)로 대체한다. 외부 주소라 referrer를 보내지 않는다. */
export function BookCover({ book }: { book: Book }) {
  const [failed, setFailed] = useState(false)
  if (book.cover_url && !failed) {
    return <img className="book-cover" src={book.cover_url} alt="" loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)} />
  }
  return (
    <div className={`book-cover book-cover-fallback cover-${coverIndex(book.code)}`} aria-hidden="true">
      <span className="bc-title">{book.title}</span>
      <span className="bc-author">{book.author}</span>
    </div>
  )
}

interface BookCardProps {
  book: Book
  onOpen: (b: Book) => void
  onReport: (b: Book) => void
}

export function BookCard({ book, onOpen, onReport }: BookCardProps) {
  return (
    <Card as="article" className="book-card">
      <BookCover book={book} />
      <div className="stack" style={{ gap: 4 }}>
        <button type="button" className="book-title" title={book.title} onClick={() => onOpen(book)}>
          {book.title}
        </button>
        <span className="muted small">{book.author || '저자 미상'}</span>
      </div>
      <span className="book-status">
        <Pill tone={book.available_quantity > 0 ? 'ok' : 'neu'}>{book.available_quantity > 0 ? `${book.available_quantity}권 비치` : '비치 없음'}</Pill>
        {book.lost_count > 0 && <Pill tone="lost">분실</Pill>}
      </span>
      <div className="book-actions">
        <Button variant="danger" size="sm" aria-label={`${book.title} 신고`} onClick={() => onReport(book)}>
          신고
        </Button>
      </div>
    </Card>
  )
}
