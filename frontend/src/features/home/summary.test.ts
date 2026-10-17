import { nextMeeting, nextReservation, reviewTodo } from './summary'
import type { Meeting } from '../meeting/api'
import type { Reservation } from '../room/api'
import type { Course } from '../review/api'

const now = new Date('2026-10-17T00:00:00Z')
const meeting = (id: number, slot_at: string, status: Meeting['status'] = 'confirmed') => ({ id, slot_at, status }) as Meeting
const reservation = (id: number, start_at: string, end_at: string, status: Reservation['status'] = 'approved') => ({ id, start_at, end_at, status }) as Reservation
const course = (id: number, can_review: boolean, review_deadline: string | null) => ({ id, can_review, review_deadline }) as Course

describe('홈 요약 선택', () => {
  it('다음 면담: 지난 것·취소·완료를 빼고 가장 이른 것', () => {
    const list = [
      meeting(1, '2026-10-10T06:00:00Z'), // 지남
      meeting(2, '2026-10-25T06:00:00Z'),
      meeting(3, '2026-10-20T06:00:00Z', 'pending'),
      meeting(4, '2026-10-18T06:00:00Z', 'canceled'),
      meeting(5, '2026-10-19T06:00:00Z', 'completed'),
    ]
    expect(nextMeeting(list, now)?.id).toBe(3)
    expect(nextMeeting([], now)).toBeNull()
    expect(nextMeeting([meeting(9, '2026-10-01T00:00:00Z')], now)).toBeNull()
  })

  it('회의실 요청: 끝나지 않은 대기·승인 중 가장 이른 시작', () => {
    const list = [
      reservation(1, '2026-10-16T05:00:00Z', '2026-10-16T07:00:00Z'), // 끝남
      reservation(2, '2026-10-22T05:00:00Z', '2026-10-22T07:00:00Z', 'pending'),
      reservation(3, '2026-10-20T05:00:00Z', '2026-10-20T07:00:00Z', 'rejected'),
      reservation(4, '2026-10-18T05:00:00Z', '2026-10-18T07:00:00Z'),
    ]
    expect(nextReservation(list, now)?.id).toBe(4)
    expect(nextReservation([], now)).toBeNull()
  })

  it('진행 중인 예약(끝나기 전)도 포함한다', () => {
    const r = reservation(7, '2026-10-16T23:00:00Z', '2026-10-17T02:00:00Z')
    expect(nextReservation([r], now)?.id).toBe(7)
  })

  it('작성할 후기: can_review 과정과 가장 이른 마감일', () => {
    const todo = reviewTodo([course(1, true, '2026-10-30'), course(2, false, '2026-10-01'), course(3, true, '2026-10-25'), course(4, true, null)])
    expect(todo.courses.map((c) => c.id)).toEqual([1, 3, 4])
    expect(todo.deadline).toBe('2026-10-25')
    expect(reviewTodo([course(1, false, null)])).toEqual({ courses: [], deadline: null })
  })
})
