import { Button, Modal } from '../../components'
import type { Book } from './api'
import { BookCover } from './BookCard'

/** 도서 상세: 표지·서지 정보·소개. 외부 서점 링크는 새 탭으로 연다. */
export function BookDetailModal({ book, onClose, onReport }: { book: Book | null; onClose: () => void; onReport: (b: Book) => void }) {
  return (
    <Modal
      open={book !== null}
      title={book?.title ?? ''}
      onClose={onClose}
      actions={
        book && (
          <>
            <Button variant="secondary" onClick={() => onReport(book)}>
              분실·훼손 신고
            </Button>
            <Button onClick={onClose}>닫기</Button>
          </>
        )
      }
    >
      {book && (
        <div className="book-detail">
          <BookCover book={book} />
          <dl className="meta">
            <dt>저자</dt>
            <dd>{book.author || '-'}</dd>
            <dt>출판사</dt>
            <dd>{[book.publisher, book.pub_date].filter(Boolean).join(' · ') || '-'}</dd>
            <dt>분류</dt>
            <dd>{book.category}</dd>
            <dt>비치</dt>
            <dd>
              {book.available_quantity}권
              {book.lost_count > 0 && <span className="muted small"> · 분실 신고 {book.lost_count}건 접수 중(전체 {book.quantity}권)</span>}
            </dd>
            {book.isbn && (
              <>
                <dt>ISBN</dt>
                <dd className="mono">{book.isbn}</dd>
              </>
            )}
          </dl>
        </div>
      )}
      {book?.description && <p className="body-sm book-desc">{book.description}</p>}
      {book?.link_url && (
        <a href={book.link_url} target="_blank" rel="noopener noreferrer" className="body-sm">
          서점에서 자세히 보기<span className="sr-only"> (새 창)</span> ↗
        </a>
      )}
    </Modal>
  )
}
