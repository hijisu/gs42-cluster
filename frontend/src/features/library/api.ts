import { api } from '../../lib/api'

export interface Book {
  id: number
  /** 42gslib 도서 코드(예: GSIA-IT-001) */
  code: string
  title: string
  author: string
  publisher: string
  isbn: string
  category: string
  quantity: number
  /** 접수(미처리)된 분실 신고 수와 그에 따른 비치 수(파생값). quantity는 그대로다. */
  lost_count: number
  available_quantity: number
  description: string
  cover_url: string
  link_url: string
  pub_date: string
}

export interface BookSearch {
  /** 조건에 맞는 전체 수. results는 현재 페이지의 항목이다. */
  total: number
  categories: string[]
  results: Book[]
}

// 종류·상태는 코드값. 문구는 labels.ts에서 매핑.
export type ReportKind = 'lost' | 'damaged'
export type ReportStatus = 'received' | 'resolved'
export type WishStatus = 'requested' | 'approved' | 'purchased' | 'rejected'

export interface BookReport {
  id: number
  book_id: number
  book_code: string
  book_title: string
  kind: ReportKind
  detail: string
  status: ReportStatus
  created_at: string
}

export interface BookWish {
  id: number
  title: string
  author: string
  reason: string
  link_url: string
  status: WishStatus
  /** 반려 사유 등 운영팀 메모 */
  staff_note: string
  created_at: string
}

export interface MyRequests {
  reports: BookReport[]
  wishes: BookWish[]
}

export const fetchBooks = (q: string, category: string, page = 1) => {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (category) params.set('category', category)
  params.set('page', String(page))
  const qs = params.toString()
  return api<BookSearch>(`/books/${qs ? `?${qs}` : ''}`)
}
export const fetchMyRequests = () => api<MyRequests>('/books/my-requests')
export const createReport = (body: { book_id: number; kind: ReportKind; detail: string }) => api<BookReport>('/books/reports', { method: 'POST', body })
export const createWish = (body: { title: string; author: string; reason: string; link_url: string }) => api<BookWish>('/books/wishes', { method: 'POST', body })
