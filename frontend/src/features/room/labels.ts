import type { PillTone } from '../../components/Pill'
import type { HourState, ReservationStatus } from './api'

// 상태 코드 → 표시 문구·색 사전
export const statusLabel: Record<ReservationStatus, string> = {
  pending: '승인 대기',
  approved: '승인됨',
  rejected: '반려',
  canceled: '취소됨',
}

export const statusTone: Record<ReservationStatus, PillTone> = {
  pending: 'wait',
  approved: 'ok',
  rejected: 'neu',
  canceled: 'neu',
}

export const hourStateLabel: Record<HourState, string> = {
  free: '비어 있음',
  pending: '승인 대기',
  approved: '예약 확정',
  blocked: '이용 불가',
}

export const cancelable = (s: ReservationStatus) => s === 'pending' || s === 'approved'

export const errorLabel: Record<string, string> = {
  past_time: '지난 시간은 예약할 수 없습니다.',
  outside_hours: '운영 시간(09~22시) 안에서 하루를 넘기지 않게 선택해 주세요.',
  invalid_range: '종료 시간은 시작 시간보다 늦어야 하고 30분 단위여야 합니다.',
  room_not_found: '장소를 찾을 수 없습니다. 새로고침 후 다시 시도해 주세요.',
  room_blocked: '현재 예약을 받지 않는 장소입니다.',
  room_block_conflict: '운영팀이 차단한 시간이라 예약할 수 없습니다.',
  invalid_transition: '이미 취소되었거나 처리된 예약입니다.',
  forbidden: '권한이 없습니다.',
}
