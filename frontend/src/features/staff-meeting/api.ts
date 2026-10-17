import { api } from '../../lib/api'
import type { Meeting, MeetingStatus } from '../meeting/api'

export interface StaffMember {
  id: number
  intra_id: string
  name: string
}

export interface StaffMeeting extends Meeting {
  student: { id: number; intra_id: string; name: string }
  staff_note: string
  created_at: string
}

export interface StaffMeetingType {
  id: number
  code: string
  name: string
  default_staff: { id: number; name: string } | null
}

export type StaffMeetingStatus = MeetingStatus

export const fetchStaffMeetings = (status: StaffMeetingStatus) => api<StaffMeeting[]>(`/staff/meetings?status=${status}`)
export const fetchMembers = () => api<StaffMember[]>('/staff/members')
export const confirmMeeting = (id: number, body: { location: string; staff_id?: number; note?: string }) =>
  api<StaffMeeting>(`/staff/meetings/${id}/confirm`, { method: 'POST', body })
export const proposeMeeting = (id: number, body: { proposed_at: string; note?: string; location?: string }) =>
  api<StaffMeeting>(`/staff/meetings/${id}/propose`, { method: 'POST', body })
export const fetchMyAvailability = (from: string, to: string) => api<{ slots: string[] }>(`/staff/availability?from=${from}&to=${to}`)
export const saveMyAvailability = (body: { from: string; to: string; slots: string[] }) => api<{ slots: string[] }>('/staff/availability', { method: 'PUT', body })
export const fetchStaffMeetingTypes = () => api<StaffMeetingType[]>('/staff/meeting-types')
export const saveStaffMeetingTypes = (body: { id: number; default_staff_id: number | null }[]) =>
  api<StaffMeetingType[]>('/staff/meeting-types', { method: 'PUT', body })
