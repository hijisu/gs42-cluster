import type { NotificationType } from './api'

// 알림 type 코드 → 제목 문구. 상세(시각·장소)는 서버가 만든 body를 그대로 쓴다.
export const typeTitle: Record<NotificationType, string> = {
  meeting_confirmed: '면담이 확정되었어요',
  meeting_proposed: '면담 시간이 제안되었어요',
  reservation_approved: '회의실 예약이 승인되었어요',
  reservation_rejected: '회의실 예약이 반려되었어요',
  reservation_reassigned: '회의실이 다른 장소로 배정되었어요',
  review_requested: '교육과정 후기를 남겨 주세요',
}

export const titleOf = (type: string, fallback: string): string => typeTitle[type as NotificationType] ?? fallback
