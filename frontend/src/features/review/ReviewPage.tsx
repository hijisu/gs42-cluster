import { useState } from 'react'
import { Card, Chip, Pill } from '../../components'
import { formatMonthDay } from '../../lib/datetime'
import { useCourses, useReviews } from './hooks'
import { writeState } from './labels'
import { ReviewCard } from './ReviewCard'
import { ReviewForm } from './ReviewForm'

const period = (start: string, end: string) => `${formatMonthDay(start)}–${formatMonthDay(end)}`

export function ReviewPage() {
  const courses = useCourses()
  const [courseId, setCourseId] = useState<number | null>(null)
  const { reviews, isPending, isError } = useReviews(courses.data, courseId)

  const all = courses.data ?? []
  const nameOf = (id: number) => all.find((c) => c.id === id)?.name ?? ''
  const current = all.find((c) => c.id === courseId)
  const writable = all.filter((c) => c.can_review)
  const mine = all.filter((c) => c.participating)
  const banner = writable[0]

  return (
    <>
      <div className="head">
        <div>
          <p className="label">04 · COURSE REVIEWS</p>
          <h1 className="h1" style={{ marginTop: 8 }}>교육과정 후기</h1>
          <p className="sub">경산이노베이션아카데미가 운영하는 교육과정에 참여한 교육생들의 후기예요.</p>
        </div>
      </div>

      {banner && (
        <div className="notice" role="status">
          <span className="stack" style={{ gap: 2 }}>
            <span className="label" style={{ color: 'var(--c-side-sub)' }}>
              후기 요청{banner.review_deadline ? ` · 마감 ${formatMonthDay(banner.review_deadline)}` : ''}
            </span>
            <span>
              <b>{banner.name}</b>에 참여하셨네요. 후기를 남겨 주세요.
            </span>
          </span>
          <a href="#write" className="btn teal">
            지금 작성하기
          </a>
        </div>
      )}

      {courses.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {courses.isError && <p role="alert">교육과정을 불러오지 못했습니다.</p>}

      <div className="split review-split">
        <div className="col">
          <div className="chips" role="group" aria-label="과정 필터">
            <Chip selected={courseId === null} onClick={() => setCourseId(null)}>
              전체 과정
            </Chip>
            {all.map((c) => (
              <Chip key={c.id} selected={courseId === c.id} onClick={() => setCourseId(c.id)}>
                {c.name}
              </Chip>
            ))}
          </div>

          {current && (
            <Card className="course-summary">
              <span className="stack" style={{ gap: 2 }}>
                <span className="label">{current.name}</span>
                <span className="muted small">
                  {period(current.start_date, current.end_date)} · {current.location}
                </span>
              </span>
              <span className="stats">
                <span className="stack" style={{ gap: 0 }}>
                  <span className="mono stat">{current.average_rating?.toFixed(1) ?? '-'}</span>
                  <span className="muted" style={{ fontSize: 12 }}>평균 만족도</span>
                </span>
                <span className="stack" style={{ gap: 0 }}>
                  <span className="mono stat">{current.review_count}</span>
                  <span className="muted" style={{ fontSize: 12 }}>후기 수</span>
                </span>
              </span>
            </Card>
          )}

          {isError && <p role="alert">후기를 불러오지 못했습니다.</p>}
          {!isPending && !isError && reviews.length === 0 && <p className="muted">아직 등록된 후기가 없어요.</p>}
          <div className="g2">
            {reviews.map((r) => (
              <ReviewCard key={r.id} review={r} courseName={nameOf(r.course_id)} />
            ))}
          </div>
        </div>

        <div className="col">
          <ReviewForm writable={writable} />
          <Card className="stack" style={{ gap: 8 }}>
            <h2 className="card-title">내가 참여한 과정</h2>
            {mine.length === 0 && <p className="muted">참여한 과정이 없어요.</p>}
            <div className="list">
              {mine.map((c) => {
                const s = writeState(c)
                return (
                  <div key={c.id} className="row">
                    <span style={{ fontSize: 14 }}>{c.name}</span>
                    <Pill tone={s.tone}>{s.label}</Pill>
                  </div>
                )
              })}
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
