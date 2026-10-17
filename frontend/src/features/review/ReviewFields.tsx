import { Chip, Field } from '../../components'
import type { Review } from './api'

export interface ReviewDraft {
  rating: number | null
  good: string
  bad: string
  recommend: string
  tags: string
  anonymous: boolean
}

export const emptyDraft: ReviewDraft = { rating: null, good: '', bad: '', recommend: '', tags: '', anonymous: true }

export const draftOf = (r: Review): ReviewDraft => ({ rating: r.rating, good: r.good, bad: r.bad, recommend: r.recommend_to, tags: r.tags.join(', '), anonymous: r.anonymous })

// '#인프라 입문, 실습' → ['인프라 입문', '실습'] (서버도 #·공백·중복을 정리하지만 입력 편의를 위해 미리 나눈다)
export const parseTags = (raw: string) => raw.split(',').map((t) => t.trim().replace(/^#+/, '').trim()).filter(Boolean)

export function draftErrors(d: ReviewDraft) {
  const tagList = parseTags(d.tags)
  return {
    rating: d.rating === null ? '만족도를 선택해 주세요.' : undefined,
    tags: tagList.length > 5 || tagList.some((t) => t.length > 20) ? '태그는 최대 5개, 각 20자까지 입력할 수 있어요.' : undefined,
  }
}

/** 후기 작성·수정 폼의 공통 입력 항목(제목은 없다) */
export function ReviewFields({ draft, onChange, submitted }: { draft: ReviewDraft; onChange: (next: ReviewDraft) => void; submitted: boolean }) {
  const errors = draftErrors(draft)
  const set = <K extends keyof ReviewDraft>(key: K, value: ReviewDraft[K]) => onChange({ ...draft, [key]: value })
  return (
    <>
      <fieldset className="rating-field">
        <legend>만족도</legend>
        <div className="chips" role="group" aria-label="만족도 1~5">
          {[1, 2, 3, 4, 5].map((n) => (
            <Chip key={n} selected={draft.rating === n} aria-label={`${n}점`} onClick={() => set('rating', n)}>
              {n}
            </Chip>
          ))}
        </div>
        {submitted && errors.rating && <span className="error" role="alert">{errors.rating}</span>}
      </fieldset>
      <Field label="좋았던 점" multiline style={{ minHeight: 56 }} value={draft.good} onChange={(e) => set('good', e.target.value)} />
      <Field label="아쉬운 점" multiline style={{ minHeight: 56 }} value={draft.bad} onChange={(e) => set('bad', e.target.value)} />
      <Field label="이런 분께 추천해요" placeholder="예: 인프라 직무에 관심 있는 분" value={draft.recommend} onChange={(e) => set('recommend', e.target.value)} />
      <Field label="태그" hint="쉼표로 구분, 최대 5개" placeholder="예: 인프라 입문, 실습 위주" value={draft.tags} onChange={(e) => set('tags', e.target.value)} error={submitted ? errors.tags : undefined} />
      <label className="check">
        <input type="checkbox" checked={draft.anonymous} onChange={(e) => set('anonymous', e.target.checked)} /> 익명으로 게시
      </label>
    </>
  )
}
