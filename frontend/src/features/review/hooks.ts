import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { createReview, fetchCourseReviews, fetchCourses, type Course, type Review } from './api'

const keys = {
  courses: ['courses', 'list'] as const,
  reviews: (courseId: number) => ['courses', 'reviews', courseId] as const,
}

export const useCourses = () => useQuery({ queryKey: keys.courses, queryFn: fetchCourses })

/** 선택한 과정(없으면 전체 과정)의 후기를 최신순으로 합쳐 돌려준다. */
export function useReviews(courses: Course[] | undefined, courseId: number | null) {
  const targets = (courses ?? []).filter((c) => courseId === null || c.id === courseId)
  const results = useQueries({
    queries: targets.map((c) => ({ queryKey: keys.reviews(c.id), queryFn: () => fetchCourseReviews(c.id) })),
  })
  const reviews: Review[] = results.flatMap((r) => r.data ?? []).sort((a, b) => b.created_at.localeCompare(a.created_at))
  return {
    reviews,
    isPending: courses === undefined || results.some((r) => r.isPending),
    isError: results.some((r) => r.isError),
  }
}

export function useCreateReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createReview,
    // 작성 상태·평균 만족도·후기 수와 목록을 새로 받는다.
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}
