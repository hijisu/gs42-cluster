import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createReport, createWish, fetchBooks, fetchMyRequests } from './api'

const keys = {
  books: ['books', 'search'] as const,
  // 운영 화면(staff-library)이 처리 후 ['books','my']를 무효화한다.
  mine: ['books', 'my'] as const,
}

/** 검색어·카테고리가 바뀌어도 이전 결과를 유지해 목록이 깜빡이지 않게 한다. */
export const useBooks = (q: string, category: string, enabled = true, page = 1) =>
  useQuery({ queryKey: [...keys.books, q, category, page], queryFn: () => fetchBooks(q, category, page), placeholderData: keepPreviousData, enabled })

export const useMyRequests = () => useQuery({ queryKey: keys.mine, queryFn: fetchMyRequests })

export function useCreateReport() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: createReport, onSuccess: () => qc.invalidateQueries({ queryKey: keys.mine }) })
}

export function useCreateWish() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: createWish, onSuccess: () => qc.invalidateQueries({ queryKey: keys.mine }) })
}
