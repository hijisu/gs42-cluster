import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  approve,
  createBlock,
  createDirect,
  createRoom,
  deleteBlock,
  deleteOccurrence,
  fetchBlocks,
  fetchStaffReservations,
  patchRoom,
  reassign,
  reject,
  saveRules,
  updateBlock,
  updateOccurrence,
  type BlockInput,
} from './api'

const root = ['staff', 'reservations'] as const

/** 승인 대기는 날짜와 무관하게 전체를 받아 시작 시각 순으로 보여 한 곳에서 처리한다. */
export const useStaffPending = () =>
  useQuery({
    queryKey: [...root, 'pending'],
    queryFn: () => fetchStaffReservations('', 'pending'),
    select: (list) => [...list].sort((a, b) => a.start_at.localeCompare(b.start_at)),
  })

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

// ----- 예약 차단 기간 -----
const blocksKey = ['staff', 'room-blocks'] as const
export const useBlocks = (from: string, to: string) => useQuery({ queryKey: [...blocksKey, from, to], queryFn: () => fetchBlocks(from, to) })

/** 차단이 바뀌면 목록과 교육생·운영 회의실 현황(차단 시간 표시)을 새로 받는다. */
function useRefreshBlocks() {
  const qc = useQueryClient()
  return () => Promise.all([qc.invalidateQueries({ queryKey: blocksKey }), qc.invalidateQueries({ queryKey: ['rooms'] })])
}
export function useCreateBlock() {
  const refresh = useRefreshBlocks()
  return useMutation({ mutationFn: createBlock, onSuccess: (r) => r.saved && refresh() })
}
export function useUpdateBlock() {
  const refresh = useRefreshBlocks()
  return useMutation({
    mutationFn: ({ id, body, check_only }: { id: number; body: Partial<BlockInput>; check_only: boolean }) => updateBlock(id, { ...body, check_only }),
    onSuccess: (r) => r.saved && refresh(),
  })
}
export function useUpdateOccurrence() {
  const refresh = useRefreshBlocks()
  return useMutation({
    mutationFn: ({ id, day, body, check_only }: { id: number; day: string; body: Partial<Pick<BlockInput, 'room_id' | 'start_at' | 'end_at' | 'reason'>>; check_only: boolean }) =>
      updateOccurrence(id, day, { ...body, check_only }),
    onSuccess: (r) => r.saved && refresh(),
  })
}
export function useDeleteBlock() {
  const refresh = useRefreshBlocks()
  return useMutation({ mutationFn: deleteBlock, onSuccess: refresh })
}
export function useDeleteOccurrence() {
  const refresh = useRefreshBlocks()
  return useMutation({ mutationFn: ({ id, day }: { id: number; day: string }) => deleteOccurrence(id, day), onSuccess: refresh })
}
