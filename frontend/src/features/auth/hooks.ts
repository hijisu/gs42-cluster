import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchMe, logout, mockLogin, type Role } from './api'

export const meKey = ['auth', 'me'] as const

export function useMe() {
  return useQuery({ queryKey: meKey, queryFn: fetchMe, staleTime: 60_000, retry: false })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      qc.setQueryData(meKey, null)
      qc.removeQueries({ predicate: (q) => q.queryKey[0] !== 'auth' })
    },
  })
}

export function useMockLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (role: Role) => mockLogin(role),
    onSuccess: () => qc.invalidateQueries({ queryKey: meKey }),
  })
}
