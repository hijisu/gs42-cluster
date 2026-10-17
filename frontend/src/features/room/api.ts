import { api } from '../../lib/api'

export interface Room {
  id: number
  code: string
  name: string
  capacity_note: string
  equipment: string
  status: 'open' | 'blocked'
}

export interface RoomRules {
  open_hour: number
  close_hour: number
  step_minutes: number
  usage_rules: string[]
}

export type HourState = 'free' | 'pending' | 'approved' | 'blocked'

export interface RoomAvailability {
  room: Room
  hours: { hour: number; state: HourState }[]
  reservations: { id: number; start_at: string; end_at: string; status: 'pending' | 'approved'; purpose: string; headcount: number; mine: boolean }[]
  /** 운영팀이 차단한 시간(반복 일정 포함, 그 날짜 기준) */
  closed?: { start_at: string; end_at: string; reason: string }[]
}

export interface Availability {
  date: string
  rooms: RoomAvailability[]
}

// 상태는 코드값. 문구는 labels.ts에서 매핑.
export type ReservationStatus = 'pending' | 'approved' | 'rejected' | 'canceled'

export interface Reservation {
  id: number
  room: Room
  requested_room: Room
  start_at: string
  end_at: string
  purpose: string
  headcount: number
  note: string
  status: ReservationStatus
  reject_reason: string
  conflict: boolean
}

export interface CreateReservationInput {
  room_id: number
  start_at: string
  end_at: string
  purpose: string
  headcount: number
  note: string
}

export const fetchRooms = () => api<Room[]>('/rooms')
export const fetchRules = () => api<RoomRules>('/rooms/rules')
export const fetchAvailability = (date: string) => api<Availability>(`/rooms/availability?date=${date}`)
export const fetchMyReservations = () => api<Reservation[]>('/reservations/me')
export const createReservation = (body: CreateReservationInput) => api<Reservation>('/reservations', { method: 'POST', body })
export const cancelReservation = (id: number) => api<Reservation>(`/reservations/${id}/cancel`, { method: 'POST' })
