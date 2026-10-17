import { api } from '../../lib/api'
import type { CourseStatus } from '../review/api'

export interface StaffCourse {
  id: number
  name: string
  start_date: string
  end_date: string
  location: string
  intro: string
  status: CourseStatus
  review_deadline: string | null
  participant_count: number
  reviewed_count: number
  pending_count: number
  review_rate: number | null
  participants?: { intra_id: string; reviewed: boolean }[]
}

export interface CreateCourseInput {
  name: string
  start_date: string
  end_date: string
  location: string
  intro: string
  review_deadline: string | null
  intra_ids: string[]
  csv: string
}

export interface ReviewRequestResult {
  course_id: number
  target: 'all' | 'pending'
  recipient_count: number
  recipients: string[]
}

export const fetchStaffCourses = () => api<StaffCourse[]>('/staff/courses')
export const createCourse = (body: CreateCourseInput) => api<StaffCourse>('/staff/courses', { method: 'POST', body })
/** 상태(status)는 서버가 날짜로 계산하므로 보내지 않는다. */
export type CoursePatch = Partial<Pick<StaffCourse, 'name' | 'start_date' | 'end_date' | 'location' | 'intro' | 'review_deadline'>>
export const fetchStaffCourse = (id: number) => api<StaffCourse>(`/staff/courses/${id}`)
export const patchCourse = (id: number, body: CoursePatch) => api<StaffCourse>(`/staff/courses/${id}`, { method: 'PATCH', body })
export const addParticipants = (id: number, body: { intra_ids: string[]; csv?: string }) =>
  api<{ added: string[]; existing: string[]; course: StaffCourse }>(`/staff/courses/${id}/participants`, { method: 'POST', body })
export const removeParticipant = (id: number, intraId: string) =>
  api<{ had_review: boolean; course: StaffCourse }>(`/staff/courses/${id}/participants/${encodeURIComponent(intraId)}`, { method: 'DELETE' })
export const sendReviewRequest = (id: number, body: { target: 'all' | 'pending'; message?: string }) =>
  api<ReviewRequestResult>(`/staff/courses/${id}/review-request`, { method: 'POST', body })
