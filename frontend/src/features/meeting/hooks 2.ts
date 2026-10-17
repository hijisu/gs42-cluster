import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { kstDateFromToday } from '../../lib/datetime'
import { cancelMeeting, createMeeting, fetchMeetingTypes, fetchMyMeetings, fetchSlots, type Meeting } from './api'

export const SLOT_WINDOW_DAYS = 14

const keys = {
  types: ['meetings', 'types'] as const,
  slots: ['meetings', 'slots'] as const,
  mine: ['meetings', 'me'] as const,
}

export const useMeetingTypes = () => useQuery({ queryKey: keys.types, queryFn: fetchMeetingTypes, staleTime: Infinity })

export function useSlots() {
  const from = kstDateFromToday(0)
  const to = kstDateFromToday(SLOT_WINDOW_DAYS - 1)
  return useQuery({ queryKey: [...keys.slots, from, to], queryFn: () => fetchSlots(from, to) })
}

export const useMyMeetings = () => useQuery({ queryKey: keys.mine, queryFn: fetchMyMeetings })

export function useCreateMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createMeeting,
    onSuccess: (created) => {
      // 신청하면 내역에 즉시 반영한다.
      qc.setQueryData<Meeting[]>(keys.mine, (old) => [created, ...(old ?? [])])
    },
    // 성공·실패(마감 409 등) 모두 슬롯 현황을 다시 받는다.
    onSettled: () => qc.invalidateQueries({ queryKey: keys.slots }),
  })
}

export function useCancelMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: cancelMeeting,
    onSuccess: (updated) => {
      qc.setQueryData<Meeting[]>(keys.mine, (old) => old?.map((m) => (m.id === updated.id ? updated : m)))
      qc.invalidateQueries({ queryKey: keys.slots })
    },
  })
}
