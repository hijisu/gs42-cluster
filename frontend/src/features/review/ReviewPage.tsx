import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, Pill, Table, type Column } from '../../components'
import { formatMonthDay } from '../../lib/datetime'
import type { Course, Review } from './api'
import { useCourses, useReviews } from './hooks'
import { ReviewCard } from './ReviewCard'
import { ReviewDetailModal, ReviewEditModal, ReviewForm } from './ReviewModal'
import { writeState } from './labels'
import { sortCourses, sortOptions, type CourseSort } from './sort'

const period = (c: Course) => `${formatMonthDay(c.start_date)}–${formatMonthDay(c.end_date)}`

/** 교육과정 후기 게시판: ① 교육과정 목록 → ② 과정을 고르면 그 과정의 후기 목록. 선택 과정은 주소(?course=)에 둔다. */
export function ReviewPage() {
  const courses = useCourses()
  const [params, setParams] = useSearchParams()
  const [sort, setSort] = useState<CourseSort>('reg')
  const [opened, setOpened] = useState<Review | null>(null)
  const [editing, setEditing] = useState<Review | null>(null)
  const courseId = Number(params.get('course')) || null
  const all = courses.data ?? []
  const current = all.find((c) => c.id === courseId) ?? null
  const reviews = useReviews(current?.id ?? null)
  const open = (id: number | null) => {
    const p = new URLSearchParams()
    if (id !== null) p.set('course', String(id))
    setParams(p)
  }
  const banner = all.find((c) => c.can_review)
  const mine = all.filter((c) => c.participating)

  const columns: Column<Course>[] = [
    {
      key: 'name',
      header: '교육과정명',
      render: (c) => (
        <span style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button type="button" className="link" onClick={() => open(c.id)}>{c.name}</button>
          {c.can_review && <Pill tone="wait">작성 가능</Pill>}
        </span>
      ),
    },
    { key: 'period', header: '교육기간', render: (c) => <span className="mono">{period(c)}</span> },
    { key: 'loc', header: '교육장소', render: (c) => c.location || '-' },
    { key: 'count', header: '후기 수', render: (c) => <span className="mono">{c.review_count}</span> },
  ]

  return (
    <>
      {current ? (
        <div className="stack" style={{ gap: 8 }}>
          <button type="button" className="crumb" onClick={() => open(null)}>
            ← 교육과정 목록
          </button>
          <div className="head">
            <div>
              <p className="label">04 · COURSE REVIEWS</p>
              <h1 className="h1" style={{ marginTop: 8 }}>{current.name}</h1>
              <p className="sub">
                {period(current)} · {current.location || '장소 미정'} · 후기 {current.review_count}개
                {current.average_rating !== null && ` · 평균 만족도 ${current.average_rating.toFixed(1)}`}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="head">
          <div>
            <p className="label">04 · COURSE REVIEWS</p>
            <h1 className="h1" style={{ marginTop: 8 }}>교육과정 후기</h1>
            <p className="sub">교육과정을 선택하면 그 과정의 후기 게시판으로 이동해요.</p>
          </div>
        </div>
      )}

      {!current && banner && (
        <div className="notice" role="status">
          <span className="stack" style={{ gap: 2 }}>
            <span className="label" style={{ color: 'var(--c-side-sub)' }}>
              후기 요청{banner.review_deadline ? ` · 마감 ${formatMonthDay(banner.review_deadline)}` : ''}
            </span>
            <span>
              <b>{banner.name}</b>에 참여하셨네요. 후기를 남겨 주세요.
            </span>
          </span>
          <button type="button" className="btn ondark" onClick={() => open(banner.id)}>
            지금 작성하기
          </button>
        </div>
      )}

      {courses.isPending && <p className="muted" role="status">불러오는 중…</p>}
      {courses.isError && <p role="alert">교육과정을 불러오지 못했습니다.</p>}
      {courseId !== null && courses.data && !current && <p className="muted">찾을 수 없는 교육과정이에요. 목록에서 다시 골라 주세요.</p>}

      {!current && courses.data && (
        <Card className="stack" style={{ gap: 12 }}>
          <div className="row">
            <h2 className="card-title">교육과정 {all.length}</h2>
            <span className="sortbar">
              <label className="small muted" htmlFor="course-sort">정렬</label>
              <select id="course-sort" className="input" value={sort} onChange={(e) => setSort(e.target.value as CourseSort)}>
                {sortOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </span>
          </div>
          <Table caption="교육과정 목록" columns={columns} rows={sortCourses(all, sort)} rowKey={(c) => c.id} empty="등록된 교육과정이 없어요." />
        </Card>
      )}

      {current && (
        <div className="split review-split">
          <div className="col">
            <Card className="course-summary">
              <span className="stack" style={{ gap: 2 }}>
                <span className="label">{current.name}</span>
                <span className="muted small">
                  {period(current)} · {current.location || '장소 미정'}
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
            {reviews.isError && <p role="alert">후기를 불러오지 못했습니다.</p>}
            {!reviews.isPending && !reviews.isError && reviews.reviews.length === 0 && (
              <Card>
                <p className="muted">아직 등록된 후기가 없어요.{current.can_review ? ' 첫 후기를 남겨 보세요.' : ''}</p>
              </Card>
            )}
            <div className="g2">
              {reviews.reviews.map((r) => (
                <ReviewCard key={r.id} review={r} onOpen={setOpened} onEdit={setEditing} />
              ))}
            </div>
          </div>
          <div className="col">
            <ReviewForm key={current.id} course={current} />
            <Card className="stack" style={{ gap: 4 }}>
              <h2 className="card-title">내가 참여한 과정</h2>
              {mine.length === 0 && <p className="muted">참여한 과정이 없어요.</p>}
              <div className="list">
                {mine.map((c) => {
                  const w = writeState(c)
                  return (
                    <div key={c.id} className="row" style={{ padding: '8px 0' }}>
                      <span style={{ fontSize: 14 }}>{c.name}</span>
                      <Pill tone={w.tone}>{w.label}</Pill>
                    </div>
                  )
                })}
              </div>
            </Card>
          </div>
        </div>
      )}
      <ReviewDetailModal review={opened} onClose={() => setOpened(null)} onEdit={(r) => { setOpened(null); setEditing(r) }} />
      <ReviewEditModal review={editing} onClose={() => setEditing(null)} />
    </>
  )
}
