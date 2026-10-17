import { api } from '../../lib/api'

export interface Book {
  id: number
  code: string
  title: string
  author: string
  publisher: string
  isbn: string
  category: string
  quantity: number
  description: string
  cover_url: string
  link_url: string
  pub_date: string
}

export interface BookSearch {
  total: number
  categories: string[]
  results: Book[]
}

export type BookInput = Pick<Book, 'code' | 'title' | 'category' | 'quantity' | 'author' | 'publisher'>

export type ReportKind = 'lost' | 'damaged'
export type ReportStatus = 'received' | 'resolved'
export type WishStatus = 'requested' | 'approved' | 'rejected' | 'purchased'

export interface BookReport {
  id: number
  book_id: number
  book_code: string
  book_title: string
  kind: ReportKind
  detail: string
  status: ReportStatus
  created_at: string
  reporter: { intra_id: string; name: string }
}

export interface BookWish {
  id: number
  title: string
  author: string
  reason: string
  link_url: string
  status: WishStatus
  staff_note: string
  created_at: string
  requester: { intra_id: string; name: string }
}

export const searchBooks = (q: string) => api<BookSearch>(`/books/?q=${encodeURIComponent(q)}`)
export const createBook = (body: BookInput) => api<Book>('/staff/books', { method: 'POST', body })
export const updateBook = (id: number, body: Partial<BookInput>) => api<Book>(`/staff/books/${id}`, { method: 'PATCH', body })
export const deleteBook = (id: number) => api<void>(`/staff/books/${id}`, { method: 'DELETE' })
export const fetchReports = () => api<BookReport[]>('/staff/book-reports')
export const resolveReport = (id: number) => api<BookReport>(`/staff/book-reports/${id}/resolve`, { method: 'POST' })
export const fetchWishes = () => api<BookWish[]>('/staff/book-wishes')
export const updateWish = (id: number, body: { status: WishStatus; note?: string }) =>
  api<BookWish>(`/staff/book-wishes/${id}`, { method: 'PATCH', body })
