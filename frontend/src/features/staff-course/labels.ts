import type { PillTone } from '../../components/Pill'
import type { StaffCourse } from './api'

/** 상태 코드 + 마감일 → 표시 문구·색 (upcoming=모집·수요조사, completed+마감 전=후기 수집 중, completed+마감 후=종료) */
export function courseState(c: StaffCourse, today: string): { label: string; tone: PillTone } {
  if (c.status === 'upcoming') return { label: '모집 · 수요조사', tone: 'neu' }
  if (c.status === 'ongoing') return { label: '진행 중', tone: 'ok' }
  if (c.review_deadline && c.review_deadline < today) return { label: '종료', tone: 'neu' }
  return { label: '후기 수집 중', tone: 'wait' }
}

/** 후기 요청을 보낼 수 있는 과정: 종료 처리됨 + 마감 전 */
export const canRequest = (c: StaffCourse, today: string) => c.status === 'completed' && !(c.review_deadline && c.review_deadline < today)

export const errorLabel: Record<string, string> = {
  invalid_course: '과정 정보를 확인해 주세요(과정명, 종료일 ≥ 시작일, 마감일 ≥ 종료일).',
  invalid_intra_id: 'intra ID 형식이 올바르지 않아요. 아무도 추가되지 않았어요.',
  review_closed: '후기를 받는 중인 과정(종료 처리 + 마감 전)만 요청을 보낼 수 있어요.',
  course_not_found: '교육과정을 찾을 수 없어요.',
}
