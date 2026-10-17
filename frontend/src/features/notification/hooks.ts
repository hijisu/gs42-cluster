import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchNotifications, markAllRead, markRead } from './api'

const key = ['notifications'] as const

/** 30초마다 새 알림을 확인한다(웹 푸시는 별도 이슈). */
export const useNotifications = (enabled = true) =>
  useQuery({ queryKey: key, queryFn: fetchNotifications, refetchInterval: 30_000, enabled })

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: markRead, onSuccess: () => qc.invalidateQueries({ queryKey: key }) })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: markAllRead, onSuccess: () => qc.invalidateQueries({ queryKey: key }) })
}
