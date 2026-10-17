import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  confirmMeeting,
  fetchMembers,
  fetchMyAvailability,
  fetchStaffMeetingTypes,
  fetchStaffMeetings,
  proposeMeeting,
  saveMyAvailability,
  saveStaffMeetingTypes,
  type StaffMeetingStatus,
} from './api'
import { tabs } from './labels'

const root = ['staff', 'meetings'] as const
const listKey = (s: StaffMeetingStatus) => [...root, 'list', s] as const

export const useStaffMeetings = (status: StaffMeetingStatus) => useQuery({ queryKey: listKey(status), queryFn: () => fetchStaffMeetings(status) })

/** 탭 숫자(신규·조율)용 건수 */
export function useTabCounts(): Partial<Record<StaffMeetingStatus, number>> {
  const counted = tabs.filter((t) => t.counted)
  const results = useQueries({ queries: counted.map((t) => ({ queryKey: listKey(t.status), queryFn: () => fetchStaffMeetings(t.status) })) })
  return Object.fromEntries(counted.map((t, i) => [t.status, results[i].data?.length]))
}

export const useMembers = () => useQuery({ queryKey: ['staff', 'members'], queryFn: fetchMembers, staleTime: Infinity })
export const useStaffMeetingTypes = () => useQuery({ queryKey: ['staff', 'meeting-types'], queryFn: fetchStaffMeetingTypes })
export const useMyAvailability = (from: string, to: string) =>
  useQuery({ queryKey: ['staff', 'availability', from, to], queryFn: () => fetchMyAvailability(from, to) })

function useRefresh() {
  const qc = useQueryClient()
  // 상태가 바뀌면 모든 탭 목록을 새로 받는다(오류로 이미 처리된 요청일 때도).
  return () => qc.invalidateQueries({ queryKey: root })
}

export function useConfirm() {
  const refresh = useRefresh()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number; location: string; staff_id?: number; note?: string }) => confirmMeeting(id, body),
    onSuccess: refresh,
    onError: (e) => {
      if ((e as { code?: string }).code === 'invalid_transition') refresh()
    },
  })
}

export function usePropose() {
  const refresh = useRefresh()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number; proposed_at: string; note?: string; location?: string }) => proposeMeeting(id, body),
    onSuccess: refresh,
    onError: (e) => {
      if ((e as { code?: string }).code === 'invalid_transition') refresh()
    },
  })
}

export function useSaveAvailability() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: saveMyAvailability, onSuccess: () => qc.invalidateQueries({ queryKey: ['staff', 'availability'] }) })
}

export function useSaveDefaultStaff() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: saveStaffMeetingTypes, onSuccess: () => qc.invalidateQueries({ queryKey: ['staff', 'meeting-types'] }) })
}
