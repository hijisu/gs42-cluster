import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createReview, fetchCourseReviews, fetchCourses, updateReview, type UpdateReviewInput } from './api'

const keys = {
  courses: ['courses', 'list'] as const,
  reviews: (courseId: number) => ['courses', 'reviews', courseId] as const,
}

export const useCourses = () => useQuery({ queryKey: keys.courses, queryFn: fetchCourses })

/** 한 과정의 후기를 최신순으로 돌려준다(과정 게시판). */
export function useReviews(courseId: number | null) {
  const q = useQuery({
    queryKey: keys.reviews(courseId ?? 0),
    queryFn: () => fetchCourseReviews(courseId as number),
    enabled: courseId !== null,
    select: (list) => [...list].sort((a, b) => b.created_at.localeCompare(a.created_at)),
  })
  return { reviews: q.data ?? [], isPending: q.isPending, isError: q.isError }
}

export function useCreateReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createReview,
    // 작성 상태·평균 만족도·후기 수와 목록을 새로 받는다.
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}

export function useUpdateReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: UpdateReviewInput }) => updateReview(id, body),
    // 만족도가 바뀌면 평균도 바뀌므로 과정·후기 조회를 모두 새로 받는다.
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}
