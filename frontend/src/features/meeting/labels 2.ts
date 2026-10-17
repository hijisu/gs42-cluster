import type { PillTone } from '../../components/Pill'
import type { MeetingStatus } from './api'

// 상태 코드 → 표시 문구·색 사전
export const statusLabel: Record<MeetingStatus, string> = {
  pending: '배정 중',
  proposed: '시간 조율 중',
  confirmed: '확정',
  completed: '완료',
  canceled: '취소됨',
}

export const statusTone: Record<MeetingStatus, PillTone> = {
  pending: 'wait',
  proposed: 'wait',
  confirmed: 'ok',
  completed: 'neu',
  canceled: 'neu',
}

/** 취소할 수 있는 상태(완료·이미 취소는 불가) */
export const cancelable = (s: MeetingStatus) => s === 'pending' || s === 'proposed' || s === 'confirmed'

// API 오류 코드 → 안내 문구
export const errorLabel: Record<string, string> = {
  slot_unavailable: '방금 마감된 시간입니다. 다른 시간을 선택해 주세요.',
  invalid_slot: '선택할 수 없는 시간입니다.',
  meeting_type_not_found: '면담 유형을 찾을 수 없습니다. 새로고침 후 다시 시도해 주세요.',
  invalid_transition: '이미 취소되었거나 완료된 면담입니다.',
  forbidden: '권한이 없습니다.',
}
