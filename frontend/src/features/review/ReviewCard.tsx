import { Card, Pill } from '../../components'
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

/** 과정 게시판의 후기 한 건. 제목 없이 만족도·본문·작성자를 보여준다. */
export function ReviewCard({ review }: { review: Review }) {
  return (
    <Card as="article" className="stack" style={{ gap: 12 }}>
      <div className="row">
        <b className="mono">{review.mine ? '내 후기' : review.anonymous || !review.author ? '익명' : review.author.intra_id}</b>
        <RatingDots value={review.rating} />
      </div>
      {review.good && <p className="body-sm"><b>좋았던 점</b> {review.good}</p>}
      {review.bad && <p className="muted body-sm"><b>아쉬운 점</b> {review.bad}</p>}
      {review.recommend_to && <p className="muted body-sm"><b>추천 대상</b> {review.recommend_to}</p>}
      {review.tags.length > 0 && (
        <div className="chips" style={{ gap: 6 }}>
          {review.tags.map((t) => (
            <Pill key={t}>#{t}</Pill>
          ))}
        </div>
      )}
      <span className="muted small mono">{kstDate(review.created_at)}</span>
    </Card>
  )
}
