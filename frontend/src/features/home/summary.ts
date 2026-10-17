import type { Meeting } from '../meeting/api'
import type { Reservation } from '../room/api'
import type { Course } from '../review/api'

// 홈 요약 카드가 고르는 '다음' 항목. 지난 것·취소/반려는 제외한다.

const ACTIVE_MEETING = new Set<Meeting['status']>(['pending', 'proposed', 'confirmed'])
const ACTIVE_RESERVATION = new Set<Reservation['status']>(['pending', 'approved'])

/** 앞으로 예정된 가장 이른 면담 */
export function nextMeeting(meetings: Meeting[], now: Date = new Date()): Meeting | null {
  return (
    meetings
      .filter((m) => ACTIVE_MEETING.has(m.status) && new Date(m.slot_at).getTime() >= now.getTime())
      .sort((a, b) => a.slot_at.localeCompare(b.slot_at))[0] ?? null
  )
}

/** 아직 끝나지 않은 가장 이른 회의실 예약(대기·승인) */
export function nextReservation(reservations: Reservation[], now: Date = new Date()): Reservation | null {
  return (
    reservations
      .filter((r) => ACTIVE_RESERVATION.has(r.status) && new Date(r.end_at).getTime() >= now.getTime())
      .sort((a, b) => a.start_at.localeCompare(b.start_at))[0] ?? null
  )
}

/** 지금 후기를 쓸 수 있는 과정과, 가장 이른 마감일 */
export function reviewTodo(courses: Course[]): { courses: Course[]; deadline: string | null } {
  const todo = courses.filter((c) => c.can_review)
  const deadlines = todo.map((c) => c.review_deadline).filter((d): d is string => d !== null).sort()
  return { courses: todo, deadline: deadlines[0] ?? null }
}
