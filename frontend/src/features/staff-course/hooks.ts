import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createCourse, fetchStaffCourses, patchCourse, sendReviewRequest, type StaffCourse } from './api'

const key = ['staff', 'courses'] as const

export const useStaffCourses = () => useQuery({ queryKey: key, queryFn: fetchStaffCourses })

/** 과정이 바뀌면 교육생 쪽 과정·후기 조회도 새로 받는다. */
function useRefresh() {
  const qc = useQueryClient()
  return () => Promise.all([qc.invalidateQueries({ queryKey: key }), qc.invalidateQueries({ queryKey: ['courses'] })])
}

export function useCreateCourse() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: createCourse, onSuccess: refresh })
}

export function useOpenReviews() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: (id: number) => patchCourse(id, { status: 'completed' }), onSuccess: refresh })
}

/** 마감일이 바뀌었으면 먼저 저장하고 요청을 보낸다. */
export function useSendRequest() {
  const refresh = useRefresh()
  return useMutation({
    mutationFn: async (input: { course: StaffCourse; deadline: string | null; target: 'all' | 'pending'; message: string }) => {
      if (input.deadline !== input.course.review_deadline) await patchCourse(input.course.id, { review_deadline: input.deadline })
      return sendReviewRequest(input.course.id, { target: input.target, message: input.message.trim() || undefined })
    },
    onSettled: refresh,
  })
}
