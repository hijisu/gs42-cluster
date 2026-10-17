import { api } from '../../lib/api'

// 과정 상태는 코드값. 문구는 labels.ts에서 매핑.
export type CourseStatus = 'upcoming' | 'ongoing' | 'completed'

export interface Course {
  id: number
  name: string
  start_date: string
  end_date: string
  location: string
  intro: string
  status: CourseStatus
  review_deadline: string | null
  average_rating: number | null
  review_count: number
  participating: boolean
  reviewed: boolean
  can_review: boolean
}

export interface Review {
  id: number
  course_id: number
  rating: number
  good: string
  bad: string
  recommend_to: string
  tags: string[]
  anonymous: boolean
  author: { intra_id: string } | null
  mine: boolean
  created_at: string
}

export interface CreateReviewInput {
  course_id: number
  rating: number
  good: string
  bad: string
  recommend_to: string
  tags: string[]
  anonymous: boolean
}

export const fetchCourses = () => api<Course[]>('/courses')
export const fetchCourseReviews = (courseId: number) => api<Review[]>(`/courses/${courseId}/reviews`)
export const createReview = (body: CreateReviewInput) => api<Review>('/reviews', { method: 'POST', body })
