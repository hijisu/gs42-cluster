import { api } from '../../lib/api'
import type { Reservation, Room, RoomRules } from '../room/api'

export interface StaffReservation extends Reservation {
  user: { id: number; intra_id: string; name: string }
  created_by_staff: boolean
  conflict_ids: number[]
}

export const fetchStaffReservations = (date: string, status: string) => api<StaffReservation[]>(`/staff/reservations?date=${date}&status=${status}`)
export const approve = (id: number) => api<StaffReservation>(`/staff/reservations/${id}/approve`, { method: 'POST' })
export const reject = (id: number, reason: string) => api<StaffReservation>(`/staff/reservations/${id}/reject`, { method: 'POST', body: { reason } })
export const reassign = (id: number, roomId: number) => api<StaffReservation>(`/staff/reservations/${id}/reassign`, { method: 'POST', body: { room_id: roomId } })
export const createDirect = (body: { room_id: number; start_at: string; end_at: string; purpose: string; headcount: number; note: string }) =>
  api<StaffReservation>('/staff/reservations', { method: 'POST', body })
export const saveRules = (body: { open_hour: number; close_hour: number; usage_rules: string[] }) => api<RoomRules>('/staff/rooms/rules', { method: 'PUT', body })
export const createRoom = (body: { name: string; capacity_note: string; equipment: string }) => api<Room>('/staff/rooms', { method: 'POST', body })
export const patchRoom = (id: number, body: Partial<Pick<Room, 'name' | 'capacity_note' | 'equipment' | 'status'>>) => api<Room>(`/staff/rooms/${id}`, { method: 'PATCH', body })
