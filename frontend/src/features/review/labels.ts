import type { PillTone } from '../../components/Pill'
import type { Course } from './api'

export const courseStatusLabel = { upcoming: '예정', ongoing: '진행 중', completed: '종료' } as const

/** '내가 참여한 과정'의 작성 상태 (코드 → 문구·색) */
export function writeState(c: Course): { label: string; tone: PillTone } {
  if (c.reviewed) return { label: '작성 완료', tone: 'neu' }
  if (c.can_review) return { label: '작성 대기', tone: 'wait' }
  if (c.status === 'completed') return { label: '작성 기간 마감', tone: 'neu' }
  return { label: courseStatusLabel[c.status], tone: 'neu' }
}

export const errorLabel: Record<string, string> = {
  not_participant: '참여한 과정만 후기를 쓸 수 있습니다.',
  review_closed: '후기를 쓸 수 있는 기간이 아닙니다(종료 전이거나 마감 후).',
  already_reviewed: '이미 후기를 작성한 과정입니다.',
  course_not_found: '과정을 찾을 수 없습니다. 새로고침 후 다시 시도해 주세요.',
  not_review_author: '내가 쓴 후기만 수정할 수 있어요.',
  review_not_found: '후기를 찾을 수 없어요. 새로고침 후 다시 시도해 주세요.',
  invalid_review: '입력 내용을 확인해 주세요.',
}
