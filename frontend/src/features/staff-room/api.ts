import { api } from '../../lib/api'
import type { Reservation, Room, RoomRules } from '../room/api'

export interface StaffReservation extends Reservation {
  user: { id: number; intra_id: string; name: string }
  created_by_staff: boolean
  conflict_ids: number[]
}

export const fetchStaffReservations = (date: string, status: string) => api<StaffReservation[]>(`/staff/reservations?${date ? `date=${date}&` : ''}status=${status}`)
export const approve = (id: number) => api<StaffReservation>(`/staff/reservations/${id}/approve`, { method: 'POST' })
export const reject = (id: number, reason: string) => api<StaffReservation>(`/staff/reservations/${id}/reject`, { method: 'POST', body: { reason } })
export const reassign = (id: number, roomId: number) => api<StaffReservation>(`/staff/reservations/${id}/reassign`, { method: 'POST', body: { room_id: roomId } })
export const createDirect = (body: { room_id: number; start_at: string; end_at: string; purpose: string; headcount: number; note: string }) =>
  api<StaffReservation>('/staff/reservations', { method: 'POST', body })
export const saveRules = (body: { open_hour: number; close_hour: number; usage_rules: string[] }) => api<RoomRules>('/staff/rooms/rules', { method: 'PUT', body })
export const createRoom = (body: { name: string; capacity_note: string; equipment: string }) => api<Room>('/staff/rooms', { method: 'POST', body })
export const patchRoom = (id: number, body: Partial<Pick<Room, 'name' | 'capacity_note' | 'equipment' | 'status'>>) => api<Room>(`/staff/rooms/${id}`, { method: 'PATCH', body })

// ----- 예약 차단 기간(반복 일정). 반복 종류는 코드값, 문구는 blockLabels.ts에서 매핑 -----
export type BlockRepeat = 'none' | 'daily' | 'weekly' | 'weekdays'

export interface RoomBlock {
  id: number
  room_id: number
  start_at: string
  end_at: string
  reason: string
  repeat: BlockRepeat
  weekdays: number[] // 0=월 … 6=일
  until: string | null
  occurrences: { date: string; start_at: string; end_at: string }[]
}

export interface BlockInput {
  room_id: number
  start_at: string
  end_at: string
  reason: string
  repeat: BlockRepeat
  weekdays: number[]
  until: string | null
}

export interface BlockResult {
  block: RoomBlock
  saved: boolean
  conflicting_reservations: { id: number; room_id: number; start_at: string; end_at: string; status: string; purpose: string }[]
}

export const fetchBlocks = (from: string, to: string) => api<RoomBlock[]>(`/staff/room-blocks?from=${from}&to=${to}`)
export const createBlock = (body: BlockInput & { check_only: boolean }) => api<BlockResult>('/staff/room-blocks', { method: 'POST', body })
export const updateBlock = (id: number, body: Partial<BlockInput> & { check_only: boolean }) => api<BlockResult>(`/staff/room-blocks/${id}`, { method: 'PATCH', body })
export const deleteBlock = (id: number) => api<void>(`/staff/room-blocks/${id}`, { method: 'DELETE' })
export const updateOccurrence = (id: number, day: string, body: Partial<Pick<BlockInput, 'room_id' | 'start_at' | 'end_at' | 'reason'>> & { check_only: boolean }) =>
  api<BlockResult>(`/staff/room-blocks/${id}/occurrences/${day}`, { method: 'PATCH', body })
export const deleteOccurrence = (id: number, day: string) => api<void>(`/staff/room-blocks/${id}/occurrences/${day}`, { method: 'DELETE' })
