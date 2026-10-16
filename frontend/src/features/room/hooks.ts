import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { cancelReservation, createReservation, fetchAvailability, fetchMyReservations, fetchRooms, fetchRules, type Reservation } from './api'

const keys = {
  rooms: ['rooms', 'list'] as const,
  rules: ['rooms', 'rules'] as const,
  availability: ['rooms', 'availability'] as const,
  mine: ['rooms', 'mine'] as const,
}

export const useRooms = () => useQuery({ queryKey: keys.rooms, queryFn: fetchRooms, staleTime: Infinity })
export const useRules = () => useQuery({ queryKey: keys.rules, queryFn: fetchRules, staleTime: Infinity })
export const useAvailability = (date: string) => useQuery({ queryKey: [...keys.availability, date], queryFn: () => fetchAvailability(date) })
export const useMyReservations = () => useQuery({ queryKey: keys.mine, queryFn: fetchMyReservations })

export function useCreateReservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createReservation,
    onSuccess: (created) => qc.setQueryData<Reservation[]>(keys.mine, (old) => [created, ...(old ?? [])]),
    // 타임라인에 '승인 대기'가 바로 보이도록 현황을 다시 받는다.
    onSettled: () => qc.invalidateQueries({ queryKey: keys.availability }),
  })
}

export function useCancelReservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: cancelReservation,
    onSuccess: (updated) => {
      qc.setQueryData<Reservation[]>(keys.mine, (old) => old?.map((r) => (r.id === updated.id ? updated : r)))
      qc.invalidateQueries({ queryKey: keys.availability })
    },
  })
}
