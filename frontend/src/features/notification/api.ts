import { api } from '../../lib/api'

// 알림 type은 코드값. 문구는 labels.ts에서 매핑.
export type NotificationType =
  | 'meeting_confirmed'
  | 'meeting_proposed'
  | 'reservation_approved'
  | 'reservation_rejected'
  | 'reservation_reassigned'
  | 'review_requested'

export interface AppNotification {
  id: number
  type: NotificationType
  title: string
  body: string
  link: string
  data: Record<string, unknown>
  read: boolean
  read_at: string | null
  created_at: string
}

export interface NotificationList {
  unread_count: number
  items: AppNotification[]
}

export const fetchNotifications = () => api<NotificationList>('/notifications?limit=50')
export const markRead = (id: number) => api<AppNotification>(`/notifications/${id}/read`, { method: 'POST' })
export const markAllRead = () => api<{ updated: number }>('/notifications/read-all', { method: 'POST' })
