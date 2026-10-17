import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { addParticipants, createCourse, fetchStaffCourse, fetchStaffCourses, patchCourse, removeParticipant, sendReviewRequest, type CoursePatch, type StaffCourse } from './api'

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

/** 수정 화면용 상세(참여자 목록 포함) */
export const useStaffCourse = (id: number | null) =>
  useQuery({ queryKey: [...key, id], queryFn: () => fetchStaffCourse(id as number), enabled: id !== null })

export function useUpdateCourse() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: ({ id, body }: { id: number; body: CoursePatch }) => patchCourse(id, body), onSuccess: refresh })
}

export function useAddParticipants() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: ({ id, intraIds, csv }: { id: number; intraIds?: string[]; csv?: string }) => addParticipants(id, { intra_ids: intraIds ?? [], csv }), onSuccess: refresh })
}

export function useRemoveParticipant() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: ({ id, intraId }: { id: number; intraId: string }) => removeParticipant(id, intraId), onSuccess: refresh })
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
