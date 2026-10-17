import { ApiError, api } from '../../lib/api'

// 역할은 문구가 아니라 코드로 받는다(student | staff).
export type Role = 'student' | 'staff'

export interface Me {
  id: number
  intra_id: string
  name: string
  role: Role
  slack_id: string | null
  image_url?: string
}

/** 미로그인(401)이면 null. CSRF 쿠키도 이 응답에서 발급된다. */
export async function fetchMe(): Promise<Me | null> {
  try {
    return await api<Me>('/auth/me')
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null
    throw e
  }
}

export const logout = () => api<void>('/auth/logout', { method: 'POST' })

/** DJANGO_DEBUG=true 개발 환경 전용 */
export const mockLogin = (role: Role) => api<{ intra_id: string; role: Role }>('/auth/mock-login', { method: 'POST', body: { role } })

export const loginUrl = `${import.meta.env.VITE_API_BASE_URL ?? '/api'}/auth/login`
