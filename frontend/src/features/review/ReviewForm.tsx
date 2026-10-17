import { useState, type FormEvent } from 'react'
import { Button, Card, Chip, Field } from '../../components'
import { ApiError } from '../../lib/api'
import type { Course } from './api'
import { useCreateReview } from './hooks'
import { errorLabel } from './labels'

// '#인프라 입문, 실습' → ['인프라 입문', '실습'] (서버도 #·공백·중복을 정리하지만 입력 편의를 위해 미리 나눈다)
const parseTags = (raw: string) => raw.split(',').map((t) => t.trim().replace(/^#+/, '').trim()).filter(Boolean)

export function ReviewForm({ writable }: { writable: Course[] }) {
  const create = useCreateReview()
  const [courseId, setCourseId] = useState<number | null>(null)
  const [rating, setRating] = useState<number | null>(null)
  const [title, setTitle] = useState('')
  const [good, setGood] = useState('')
  const [bad, setBad] = useState('')
  const [recommend, setRecommend] = useState('')
  const [tags, setTags] = useState('')
  const [anonymous, setAnonymous] = useState(true)
  const [submitted, setSubmitted] = useState(false)

  const selected = courseId !== null && writable.some((c) => c.id === courseId) ? courseId : (writable[0]?.id ?? null)
  const tagList = parseTags(tags)
  const errors = {
    rating: rating === null ? '만족도를 선택해 주세요.' : undefined,
    title: title.trim() === '' ? '제목을 입력해 주세요.' : undefined,
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
    if (selected === null || rating === null || errors.title || errors.tags) return
    create.mutate(
      { course_id: selected, rating, title: title.trim(), good: good.trim(), bad: bad.trim(), recommend_to: recommend.trim(), tags: tagList, anonymous },
      {
        onSuccess: () => {
          setCourseId(null)
          setRating(null)
          setTitle('')
          setGood('')
          setBad('')
          setRecommend('')
          setTags('')
          setSubmitted(false)
        },
      },
    )
  }

  return (
    <Card>
      <form id="write" className="stack" onSubmit={onSubmit} noValidate>
        <h2 className="card-title">후기 작성</h2>
        {writable.length === 0 ? (
          <p className="muted">지금 후기를 작성할 수 있는 과정이 없어요. 참여한 과정이 끝나면 작성할 수 있어요.</p>
        ) : (
          <>
            <div className="field">
              <label htmlFor="review-course">교육과정</label>
              <select id="review-course" className="input" value={selected ?? ''} onChange={(e) => setCourseId(Number(e.target.value))}>
                {writable.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <span className="muted small">참여한 과정만 선택할 수 있어요</span>
            </div>
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
            <Field label="제목" value={title} onChange={(e) => setTitle(e.target.value)} error={submitted ? errors.title : undefined} />
            <Field label="좋았던 점" multiline value={good} onChange={(e) => setGood(e.target.value)} />
            <Field label="아쉬운 점" multiline value={bad} onChange={(e) => setBad(e.target.value)} />
            <Field label="이런 분께 추천해요" placeholder="예: 인프라 직무에 관심 있는 분" value={recommend} onChange={(e) => setRecommend(e.target.value)} />
            <Field label="태그" hint="쉼표로 구분, 최대 5개" placeholder="예: 인프라 입문, 실습 위주" value={tags} onChange={(e) => setTags(e.target.value)} error={submitted ? errors.tags : undefined} />
            <label className="check">
              <input type="checkbox" checked={anonymous} onChange={(e) => setAnonymous(e.target.checked)} /> 익명으로 게시
            </label>
            {submitError && <p role="alert" className="login-error">{submitError}</p>}
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? '등록 중…' : '후기 등록'}
            </Button>
          </>
        )}
      </form>
    </Card>
  )
}
