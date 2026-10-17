import { api } from '../../lib/api'

export interface MeetingType {
  id: number
  code: string
  name: string
}

/** state: open=신청 가능, full=마감(자리 없음·지난 시간), unavailable=불가(연 담당자 없음) */
export type SlotState = 'open' | 'full' | 'unavailable'

export interface Slot {
  start_at: string
  state: SlotState
  available: boolean
  remaining: number
}

// 상태는 코드값으로 받는다. 문구는 labels.ts에서 매핑.
export type MeetingStatus = 'pending' | 'proposed' | 'confirmed' | 'completed' | 'canceled'

export interface Meeting {
  id: number
  type: MeetingType
  slot_at: string
  content: string
  notify_slack: boolean
  status: MeetingStatus
  staff: { id: number; name: string } | null
  location: string
  proposed_at: string | null
}

export interface CreateMeetingInput {
  type_id: number
  slot_at: string
  content: string
  notify_slack: boolean
}

export const fetchMeetingTypes = () => api<MeetingType[]>('/meetings/types')
export const fetchSlots = (from: string, to: string) => api<Slot[]>(`/meetings/slots?from=${from}&to=${to}`)
export const fetchMyMeetings = () => api<Meeting[]>('/meetings/me')
export const createMeeting = (body: CreateMeetingInput) => api<Meeting>('/meetings', { method: 'POST', body })
export const cancelMeeting = (id: number) => api<Meeting>(`/meetings/${id}/cancel`, { method: 'POST' })

export const acceptMeetingProposal = (id: number) => api<Meeting>(`/meetings/${id}/accept`, { method: 'POST' })
