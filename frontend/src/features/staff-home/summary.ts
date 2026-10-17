import { kstDate } from '../../lib/datetime'
import type { StaffCourse } from '../staff-course/api'
import type { BookReport, BookWish } from '../staff-library/api'
import type { StaffMeeting } from '../staff-meeting/api'
import type { StaffReservation } from '../staff-room/api'

export type TodoKind = 'meeting' | 'room' | 'wish' | 'report'

export interface TodoItem {
  key: string
  kind: TodoKind
  who: string
  title: string
  detail: string
  to: string
}

export const todoKindLabel: Record<TodoKind, string> = { meeting: '면담', room: '회의실', wish: '희망 도서', report: '분실·훼손 신고' }

/** 종류별 최신 순으로 최대 `limit`건씩, 종류 순서(면담→회의실→도서)로 이어 붙인다. */
export const MAX_PER_KIND = 3

export function pendingMeetings(list: StaffMeeting[]): StaffMeeting[] {
  return list.filter((m) => m.status === 'pending')
}

export function todoItems(input: {
  meetings: StaffMeeting[]
  reservations: StaffReservation[]
  wishes: BookWish[]
  reports: BookReport[]
}): TodoItem[] {
  const newest = <T extends { created_at: string }>(rows: T[]) => [...rows].sort((a, b) => b.created_at.localeCompare(a.created_at))
  const meetings = newest(input.meetings).slice(0, MAX_PER_KIND).map<TodoItem>((m) => ({
    key: `m${m.id}`, kind: 'meeting', who: m.student.intra_id, title: m.type.name, detail: m.slot_at, to: '/staff/meeting',
  }))
  const rooms = [...input.reservations].sort((a, b) => a.start_at.localeCompare(b.start_at)).slice(0, MAX_PER_KIND).map<TodoItem>((r) => ({
    key: `r${r.id}`, kind: 'room', who: r.user.intra_id, title: r.room.name, detail: r.start_at, to: '/staff/room',
  }))
  const wishes = newest(input.wishes.filter((w) => w.status === 'requested')).slice(0, MAX_PER_KIND).map<TodoItem>((w) => ({
    key: `w${w.id}`, kind: 'wish', who: w.requester.intra_id, title: w.title, detail: '', to: '/staff/library',
  }))
  const reports = newest(input.reports.filter((r) => r.status === 'received')).slice(0, MAX_PER_KIND).map<TodoItem>((r) => ({
    key: `p${r.id}`, kind: 'report', who: r.reporter.intra_id, title: r.book_title, detail: '', to: '/staff/library',
  }))
  return [...meetings, ...rooms, ...wishes, ...reports]
}

export interface ScheduleItem {
  key: string
  kind: 'meeting' | 'room'
  at: string
  title: string
  place: string
}

/** 오늘(KST) 확정된 면담과 승인된 회의실 예약을 시작 시각 순으로. */
export function todaySchedule(meetings: StaffMeeting[], reservations: StaffReservation[], today: string): ScheduleItem[] {
  const items: ScheduleItem[] = [
    ...meetings.filter((m) => m.status === 'confirmed' && kstDate(m.slot_at) === today).map<ScheduleItem>((m) => ({
      key: `m${m.id}`, kind: 'meeting', at: m.slot_at, title: `${m.type.name} · ${m.student.intra_id}`, place: m.location,
    })),
    ...reservations.filter((r) => r.status === 'approved' && kstDate(r.start_at) === today).map<ScheduleItem>((r) => ({
      key: `r${r.id}`, kind: 'room', at: r.start_at, title: `${r.room.name} · ${r.purpose}`, place: r.user.intra_id,
    })),
  ]
  return items.sort((a, b) => a.at.localeCompare(b.at))
}

/** 후기를 받고 있는(종료 처리됨) 과정 중 가장 최근 과정의 작성률. */
export function latestReviewRate(courses: StaffCourse[]): { name: string; percent: number } | null {
  const rated = courses
    .filter((c) => c.status === 'completed' && c.review_rate !== null)
    .sort((a, b) => b.end_date.localeCompare(a.end_date))[0]
  return rated ? { name: rated.name, percent: Math.round((rated.review_rate ?? 0) * 100) } : null
}
