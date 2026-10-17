import type { PillTone } from '../../components/Pill'
import type { ReportKind, WishStatus } from './api'

export const reportKindLabel: Record<ReportKind, string> = { lost: '분실', damaged: '훼손' }

export const wishStatusLabel: Record<WishStatus, { label: string; tone: PillTone }> = {
  requested: { label: '접수', tone: 'wait' },
  approved: { label: '검토 중', tone: 'neu' },
  purchased: { label: '구매 확정', tone: 'ok' },
  rejected: { label: '반려', tone: 'done' },
}

/** 이미 비치된 도서라는 반려 사유(버튼 한 번으로 반려) */
export const ALREADY_OWNED_NOTE = '이미 비치된 도서입니다'

export const errorLabel: Record<string, string> = {
  duplicate_book: '이미 있는 도서 코드예요.',
  invalid_book: '도서 코드·제목·수량을 확인해 주세요.',
  invalid_transition: '이미 처리된 항목이에요. 화면을 새로 고쳐 주세요.',
  invalid_wish: '반려 사유를 입력해 주세요.',
  book_not_found: '도서를 찾을 수 없어요.',
}
