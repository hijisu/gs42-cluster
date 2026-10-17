import type { PillTone } from '../../components/Pill'
import type { ReportKind, ReportStatus, WishStatus } from './api'

// 코드 → 표시 문구·색 사전
export const reportKindLabel: Record<ReportKind, string> = { lost: '분실', damaged: '훼손' }
export const reportKindOption: Record<ReportKind, string> = { lost: '서가에 없음 (분실)', damaged: '훼손' }

export const reportStatusLabel: Record<ReportStatus, string> = { received: '확인 중', resolved: '처리 완료' }
export const reportStatusTone: Record<ReportStatus, PillTone> = { received: 'wait', resolved: 'neu' }

// 운영 화면(staff-library)과 같은 문구: 접수 → 검토 중 → 구매 확정 / 반려
export const wishStatusLabel: Record<WishStatus, string> = { requested: '접수', approved: '검토 중', purchased: '구매 확정', rejected: '반려' }
export const wishStatusTone: Record<WishStatus, PillTone> = { requested: 'wait', approved: 'neu', purchased: 'ok', rejected: 'done' }

export const errorLabel: Record<string, string> = {
  book_not_found: '도서를 찾을 수 없어요. 새로고침 후 다시 시도해 주세요.',
  invalid_report: '훼손 신고에는 훼손 내용을 적어 주세요.',
  invalid_wish: '도서명을 입력해 주세요.',
}
