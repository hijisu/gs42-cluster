import { useState, type FormEvent } from 'react'
import { Button, Chip, Field, Modal } from '../../components'
import { ApiError } from '../../lib/api'
import type { Course } from './api'
import { useCreateReview } from './hooks'
import { errorLabel } from './labels'

// '#인프라 입문, 실습' → ['인프라 입문', '실습'] (서버도 #·공백·중복을 정리하지만 입력 편의를 위해 미리 나눈다)
const parseTags = (raw: string) => raw.split(',').map((t) => t.trim().replace(/^#+/, '').trim()).filter(Boolean)

/** 후기 작성(팝업). 과정 게시판에서 그 과정의 후기를 쓴다. 제목은 없다. */
export function ReviewModal({ course, open, onClose }: { course: Course; open: boolean; onClose: () => void }) {
  const create = useCreateReview()
  const [rating, setRating] = useState<number | null>(null)
  const [good, setGood] = useState('')
  const [bad, setBad] = useState('')
  const [recommend, setRecommend] = useState('')
  const [tags, setTags] = useState('')
  const [anonymous, setAnonymous] = useState(true)
  const [submitted, setSubmitted] = useState(false)

  const tagList = parseTags(tags)
  const errors = {
    rating: rating === null ? '만족도를 선택해 주세요.' : undefined,
    tags: tagList.length > 5 || tagList.some((t) => t.length > 20) ? '태그는 최대 5개, 각 20자까지 입력할 수 있어요.' : undefined,
  }

  const submitError =
    create.error instanceof ApiError
      ? (errorLabel[create.error.code ?? ''] ?? '등록하지 못했습니다. 잠시 후 다시 시도해 주세요.')
      : create.isError
        ? '등록하지 못했습니다. 잠시 후 다시 시도해 주세요.'
        : null

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitted(true)
    if (rating === null || errors.tags) return
    create.mutate(
      { course_id: course.id, rating, good: good.trim(), bad: bad.trim(), recommend_to: recommend.trim(), tags: tagList, anonymous },
      {
        onSuccess: () => {
          setRating(null)
          setGood('')
          setBad('')
          setRecommend('')
          setTags('')
          setSubmitted(false)
          onClose()
        },
      },
    )
  }

  return (
    <Modal open={open} title="후기 작성" onClose={onClose}>
      <form className="stack" onSubmit={onSubmit} noValidate>
        <p className="muted small">{course.name}</p>
        <fieldset className="rating-field">
          <legend>만족도</legend>
          <div className="chips" role="group" aria-label="만족도 1~5">
            {[1, 2, 3, 4, 5].map((n) => (
              <Chip key={n} selected={rating === n} aria-label={`${n}점`} onClick={() => setRating(n)}>
                {n}
              </Chip>
            ))}
          </div>
          {submitted && errors.rating && <span className="error" role="alert">{errors.rating}</span>}
        </fieldset>
        <Field label="좋았던 점" multiline value={good} onChange={(e) => setGood(e.target.value)} />
        <Field label="아쉬운 점" multiline value={bad} onChange={(e) => setBad(e.target.value)} />
        <Field label="이런 분께 추천해요" placeholder="예: 인프라 직무에 관심 있는 분" value={recommend} onChange={(e) => setRecommend(e.target.value)} />
        <Field label="태그" hint="쉼표로 구분, 최대 5개" placeholder="예: 인프라 입문, 실습 위주" value={tags} onChange={(e) => setTags(e.target.value)} error={submitted ? errors.tags : undefined} />
        <label className="check">
          <input type="checkbox" checked={anonymous} onChange={(e) => setAnonymous(e.target.checked)} /> 익명으로 게시
        </label>
        {submitError && <p role="alert" className="login-error">{submitError}</p>}
        <div className="modal-actions">
          <Button variant="ghost" onClick={onClose}>
            취소
          </Button>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? '등록 중…' : '후기 등록'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
