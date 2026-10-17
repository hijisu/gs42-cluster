import { useState, type FormEvent } from 'react'
import { Button, Card, Modal } from '../../components'
import { ApiError } from '../../lib/api'
import type { Course, Review } from './api'
import { useCreateReview, useUpdateReview } from './hooks'
import { errorLabel } from './labels'
import { draftErrors, draftOf, emptyDraft, parseTags, ReviewFields, type ReviewDraft } from './ReviewFields'
import { RatingDots } from './ReviewCard'

const messageOf = (error: unknown, fallback: string) =>
  error instanceof ApiError ? (errorLabel[error.code ?? ''] ?? fallback) : error ? fallback : null

/** 후기 작성(과정 게시판 오른쪽 카드). 제목은 없다. */
export function ReviewForm({ course }: { course: Course }) {
  const create = useCreateReview()
  const [draft, setDraft] = useState<ReviewDraft>(emptyDraft)
  const [submitted, setSubmitted] = useState(false)
  const errors = draftErrors(draft)
  const error = messageOf(create.error, '등록하지 못했습니다. 잠시 후 다시 시도해 주세요.')

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitted(true)
    if (draft.rating === null || errors.tags) return
    create.mutate(
      { course_id: course.id, rating: draft.rating, good: draft.good.trim(), bad: draft.bad.trim(), recommend_to: draft.recommend.trim(), tags: parseTags(draft.tags), anonymous: draft.anonymous },
      {
        onSuccess: () => {
          setDraft(emptyDraft)
          setSubmitted(false)
        },
      },
    )
  }

  return (
    <Card>
      <form id="write" className="stack" onSubmit={onSubmit} noValidate>
        <h2 className="card-title">후기 작성</h2>
        {course.can_review ? (
          <>
            <ReviewFields draft={draft} onChange={setDraft} submitted={submitted} />
            {error && <p role="alert" className="login-error">{error}</p>}
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? '등록 중…' : '후기 등록'}
            </Button>
          </>
        ) : (
          <p className="muted">{course.reviewed ? '이미 이 과정의 후기를 작성했어요. 아래 내 후기에서 수정할 수 있어요.' : '지금 이 과정의 후기를 작성할 수 없어요. 참여한 과정이 끝나면 마감 전까지 작성할 수 있어요.'}</p>
        )}
      </form>
    </Card>
  )
}

/** 내 후기 수정(팝업). 삭제는 제공하지 않는다. */
export function ReviewEditModal({ review, onClose }: { review: Review | null; onClose: () => void }) {
  return (
    <Modal open={review !== null} title="내 후기 수정" onClose={onClose}>
      {review && <EditBody key={review.id} review={review} onClose={onClose} />}
    </Modal>
  )
}

function EditBody({ review, onClose }: { review: Review; onClose: () => void }) {
  const update = useUpdateReview()
  const [draft, setDraft] = useState<ReviewDraft>(draftOf(review))
  const [submitted, setSubmitted] = useState(false)
  const errors = draftErrors(draft)
  const error = messageOf(update.error, '저장하지 못했습니다. 잠시 후 다시 시도해 주세요.')

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitted(true)
    if (draft.rating === null || errors.tags) return
    update.mutate(
      { id: review.id, body: { rating: draft.rating, good: draft.good.trim(), bad: draft.bad.trim(), recommend_to: draft.recommend.trim(), tags: parseTags(draft.tags), anonymous: draft.anonymous } },
      { onSuccess: onClose },
    )
  }

  return (
    <form className="stack" onSubmit={onSubmit} noValidate>
      <ReviewFields draft={draft} onChange={setDraft} submitted={submitted} />
      {error && <p role="alert" className="login-error">{error}</p>}
      <div className="modal-actions">
        <Button variant="secondary" onClick={onClose}>
          취소
        </Button>
        <Button type="submit" disabled={update.isPending}>
          {update.isPending ? '저장 중…' : '저장'}
        </Button>
      </div>
    </form>
  )
}

/** 후기 전문 보기(팝업). 내 후기에는 수정 버튼이 있다. */
export function ReviewDetailModal({ review, onClose, onEdit }: { review: Review | null; onClose: () => void; onEdit: (r: Review) => void }) {
  return (
    <Modal open={review !== null} title={review ? `${review.mine ? '내 후기' : review.anonymous || !review.author ? '익명' : review.author.intra_id} · 만족도 ${review.rating}/5` : '후기'} onClose={onClose}>
      {review && (
        <div className="stack">
          <RatingDots value={review.rating} />
          {review.good && <p className="body-sm"><b>좋았던 점</b> {review.good}</p>}
          {review.bad && <p className="muted body-sm"><b>아쉬운 점</b> {review.bad}</p>}
          {review.recommend_to && <p className="muted body-sm"><b>추천 대상</b> {review.recommend_to}</p>}
          {review.tags.length > 0 && <p className="muted body-sm">{review.tags.map((t) => `#${t}`).join(' ')}</p>}
          <div className="modal-actions">
            {review.mine && (
              <Button variant="secondary" onClick={() => onEdit(review)}>
                수정
              </Button>
            )}
            <Button variant="secondary" onClick={onClose}>
              닫기
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
