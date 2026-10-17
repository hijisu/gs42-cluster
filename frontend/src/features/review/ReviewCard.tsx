import type { KeyboardEvent } from 'react'
import { Button, Card } from '../../components'
import { kstDate } from '../../lib/datetime'
import type { Review } from './api'

export function RatingDots({ value }: { value: number }) {
  return (
    <span className="dots" role="img" aria-label={`만족도 ${value}/5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= value ? 'on' : ''} />
      ))}
    </span>
  )
}

interface ReviewCardProps {
  review: Review
  onOpen: (r: Review) => void
  onEdit: (r: Review) => void
}

/** 과정 게시판의 후기 한 건: '좋았던 점'은 1줄만 보이고, 카드를 누르면 전문 팝업. 내 후기에만 수정 버튼(삭제 없음). */
export function ReviewCard({ review, onOpen, onEdit }: ReviewCardProps) {
  const onKey = (e: KeyboardEvent) => {
    if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onOpen(review)
    }
  }
  const who = review.mine ? '내 후기' : review.anonymous || !review.author ? '익명' : review.author.intra_id
  return (
    <Card as="article" className="stack review-item" style={{ gap: 8 }} role="button" tabIndex={0} aria-label={`${who} 후기 전문 보기`} onClick={() => onOpen(review)} onKeyDown={onKey}>
      <div className="row">
        <b className="mono small">{who}</b>
        <RatingDots value={review.rating} />
      </div>
      <p className="body-sm clamp1">
        <b>좋았던 점</b> {review.good || '-'}
      </p>
      <div className="row">
        <span className="muted small mono">{kstDate(review.created_at)}</span>
        {review.mine && (
          <Button
            variant="secondary"
            size="sm"
            aria-label="내 후기 수정"
            onClick={(e) => {
              e.stopPropagation()
              onEdit(review)
            }}
          >
            수정
          </Button>
        )}
      </div>
    </Card>
  )
}
