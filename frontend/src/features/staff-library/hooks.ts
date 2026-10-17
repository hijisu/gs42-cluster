import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createBook, deleteBook, fetchReports, fetchWishes, resolveReport, searchBooks, updateBook, updateWish,
  type BookInput, type WishStatus,
} from './api'

const booksKey = ['staff', 'books'] as const
const reportsKey = ['staff', 'book-reports'] as const
const wishesKey = ['staff', 'book-wishes'] as const

export const useBooks = (q: string) => useQuery({ queryKey: [...booksKey, q], queryFn: () => searchBooks(q), placeholderData: (prev) => prev })
export const useReports = () => useQuery({ queryKey: reportsKey, queryFn: fetchReports })
export const useWishes = () => useQuery({ queryKey: wishesKey, queryFn: fetchWishes })

/** 도서가 바뀌면 교육생 쪽 도서 조회·내 신청 목록도 새로 받는다. */
function useRefresh(...keys: (readonly string[])[]) {
  const qc = useQueryClient()
  return () => Promise.all(keys.map((queryKey) => qc.invalidateQueries({ queryKey })))
}

export function useSaveBook() {
  const refresh = useRefresh(booksKey, ['books'])
  return useMutation({
    mutationFn: (input: { id?: number; body: BookInput }) => (input.id ? updateBook(input.id, { ...input.body, code: undefined }) : createBook(input.body)),
    onSuccess: refresh,
  })
}

export function useDeleteBook() {
  const refresh = useRefresh(booksKey, reportsKey, ['books'])
  return useMutation({ mutationFn: deleteBook, onSuccess: refresh })
}

export function useResolveReport() {
  const refresh = useRefresh(reportsKey, ['books', 'my'])
  return useMutation({ mutationFn: resolveReport, onSuccess: refresh })
}

export function useUpdateWish() {
  const refresh = useRefresh(wishesKey, ['books', 'my'])
  return useMutation({ mutationFn: (input: { id: number; status: WishStatus; note?: string }) => updateWish(input.id, { status: input.status, note: input.note }), onSuccess: refresh })
}
