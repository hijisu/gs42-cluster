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
  status: CourseStatus
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
export const patchCourse = (id: number, body: Partial<Pick<StaffCourse, 'status' | 'review_deadline'>>) =>
  api<StaffCourse>(`/staff/courses/${id}`, { method: 'PATCH', body })
export const sendReviewRequest = (id: number, body: { target: 'all' | 'pending'; message?: string }) =>
  api<ReviewRequestResult>(`/staff/courses/${id}/review-request`, { method: 'POST', body })
