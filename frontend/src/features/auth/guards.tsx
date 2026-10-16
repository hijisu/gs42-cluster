import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useMe } from './hooks'
import type { Role } from './api'

/** 로그인 필수. 미로그인이면 /login 으로 보내고 돌아올 경로를 기억한다. */
export function RequireAuth({ role }: { role?: Role }) {
  const { data: me, isPending, isError } = useMe()
  const location = useLocation()

  if (isPending) return <p className="muted" role="status" style={{ padding: 24 }}>불러오는 중…</p>
  if (isError) return <p role="alert" style={{ padding: 24 }}>사용자 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</p>
  if (!me) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  // 교육생이 운영 라우트에 접근하면 교육생 홈으로 돌려보낸다.
  if (role && me.role !== role) return <Navigate to="/" replace />
  return <Outlet />
}
