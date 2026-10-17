import { Card, Pill } from '../../components'
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

export function ReviewCard({ review, courseName }: { review: Review; courseName: string }) {
  return (
    <Card as="article" className="stack" style={{ gap: 12 }}>
      <span style={{ alignSelf: 'flex-start' }}>
        <Pill tone="ok">{courseName}</Pill>
      </span>
      <h3 style={{ fontSize: 18 }}>{review.title}</h3>
      {review.good && <p className="muted body-sm"><b>좋았던 점</b> {review.good}</p>}
      {review.bad && <p className="muted body-sm"><b>아쉬운 점</b> {review.bad}</p>}
      {review.recommend_to && <p className="muted body-sm"><b>추천 대상</b> {review.recommend_to}</p>}
      {review.tags.length > 0 && (
        <div className="chips" style={{ gap: 6 }}>
          {review.tags.map((t) => (
            <Pill key={t}>#{t}</Pill>
          ))}
        </div>
      )}
      <div className="row review-foot">
        <span className="rating-line small">
          <span className="muted">만족도</span>
          <RatingDots value={review.rating} />
        </span>
        <span className="muted small">{review.mine ? '내 후기' : review.anonymous || !review.author ? '익명' : review.author.intra_id}</span>
      </div>
    </Card>
  )
}
