import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { approve, createDirect, createRoom, fetchStaffReservations, patchRoom, reassign, reject, saveRules } from './api'

const root = ['staff', 'reservations'] as const

export const useStaffPending = (date: string) => useQuery({ queryKey: [...root, date, 'pending'], queryFn: () => fetchStaffReservations(date, 'pending') })

/** 예약 상태가 바뀌면 운영·교육생 쪽 예약/현황 조회를 모두 새로 받는다(오류로 이미 처리된 요청일 때도). */
function useRefresh() {
  const qc = useQueryClient()
  return () => Promise.all([qc.invalidateQueries({ queryKey: root }), qc.invalidateQueries({ queryKey: ['rooms'] })])
}

const onConflictRefresh = (refresh: () => unknown) => (e: unknown) => {
  if ((e as { code?: string }).code === 'invalid_transition') refresh()
}

export function useApprove() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: approve, onSuccess: refresh, onError: onConflictRefresh(refresh) })
}
export function useReject() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: ({ id, reason }: { id: number; reason: string }) => reject(id, reason), onSuccess: refresh, onError: onConflictRefresh(refresh) })
}
export function useReassign() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: ({ id, roomId }: { id: number; roomId: number }) => reassign(id, roomId), onSuccess: refresh, onError: onConflictRefresh(refresh) })
}
export function useCreateDirect() {
  const refresh = useRefresh()
  return useMutation({ mutationFn: createDirect, onSuccess: refresh })
}
export function useSaveRules() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: saveRules, onSuccess: () => qc.invalidateQueries({ queryKey: ['rooms'] }) })
}
export function useCreateRoom() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: createRoom, onSuccess: () => qc.invalidateQueries({ queryKey: ['rooms'] }) })
}
export function usePatchRoom() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ id, ...body }: { id: number; status: 'open' | 'blocked' }) => patchRoom(id, body), onSuccess: () => qc.invalidateQueries({ queryKey: ['rooms'] }) })
}
